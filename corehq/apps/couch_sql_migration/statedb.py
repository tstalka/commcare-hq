import errno
import json
import logging
import os
import os.path
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime

from memoized import memoized
from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
    Text,
    and_,
    bindparam,
    func,
    or_,
)
from sqlalchemy.exc import IntegrityError

from corehq.apps.tzmigration.planning import Base, DiffDB, PlanningDiff as Diff
from corehq.apps.tzmigration.timezonemigration import json_diff

from .diff import filter_form_diffs

log = logging.getLogger(__name__)


def init_state_db(domain, state_dir):
    db_filepath = _get_state_db_filepath(domain, state_dir)
    db_dir = os.path.dirname(db_filepath)
    if os.path.isdir(state_dir) and not os.path.isdir(db_dir):
        os.mkdir(db_dir)
    return StateDB.init(db_filepath)


def open_state_db(domain, state_dir):
    """Open state db in read-only mode"""
    db_filepath = _get_state_db_filepath(domain, state_dir)
    if not os.path.exists(db_filepath):
        db_filepath = ":memory:"
    return StateDB.open(db_filepath, readonly=True)


def delete_state_db(domain, state_dir):
    db_filepath = _get_state_db_filepath(domain, state_dir)
    try:
        os.remove(db_filepath)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def _get_state_db_filepath(domain, state_dir):
    return os.path.join(state_dir, "db", '{}-couch-sql.db'.format(domain))


class StateDB(DiffDB):

    @classmethod
    def init(cls, path):
        is_new_db = not os.path.exists(path)
        db = super(StateDB, cls).init(path)
        if is_new_db:
            db._set_kv("db_unique_id", datetime.utcnow().strftime("%Y%m%d-%H%M%S.%f"))
        return db

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.is_rebuild = False

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self):
        self.engine.dispose()

    @contextmanager
    def session(self, session=None):
        if session is not None:
            yield session
            return
        session = self.Session()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    @property
    @memoized
    def unique_id(self):
        with self.session() as session:
            return self._get_kv("db_unique_id", session).value

    def get(self, name, default=None):
        with self.session() as session:
            kv = self._get_kv(f"kv-{name}", session)
            if kv is None:
                return default
            return json.loads(kv.value)

    def set(self, name, value):
        self._upsert(KeyValue, KeyValue.key, f"kv-{name}", json.dumps(value))

    def update_cases(self, case_records):
        """Update case total and processed form counts

        :param case_records: iterable of objects, each having the attributes:

            - id: case id
            - total_forms: number of forms known to update the case.
            - processed_forms: number of forms updating the case that
              have been processed.

        :returns: list of three-tuples `(case_id, total_forms, processed_forms)`
        """
        params = [
            {"case": rec.id, "total": rec.total_forms, "proc": rec.processed_forms}
            for rec in case_records
        ]
        with self.session() as session:
            session.execute(
                """
                INSERT OR REPLACE INTO {table} (case_id, total_forms, processed_forms)
                VALUES (
                    :case,
                    MAX(COALESCE((
                        SELECT total_forms
                        FROM {table}
                        WHERE case_id = :case
                    ), 0), :total),
                    COALESCE((
                        SELECT processed_forms
                        FROM {table}
                        WHERE case_id = :case
                    ), 0) + :proc
                )
                """.format(table=CaseForms.__tablename__),
                params,
            )
            case_ids = [p["case"] for p in params]
            query = session.query(CaseForms).filter(CaseForms.case_id.in_(case_ids))
            result = [(c.case_id, c.total_forms, c.processed_forms) for c in query]
        assert len(case_ids) == len(result), (case_ids, result)
        return result

    def add_processed_forms(self, cases):
        """Increment processed forms count for each of the given cases

        :param cases: dict `{<case_id>: <processed_form_count>, ...}`
        :returns: list of three-tuples `(case_id, total_forms, processed_forms)`
        where `total_forms` is `None` for unknown cases.
        """
        case_col = CaseForms.case_id
        proc_col = CaseForms.processed_forms
        params = [{"case": c, "proc": p} for c, p in cases.items()]
        with self.session() as session:
            session.execute(
                CaseForms.__table__.update()
                .where(case_col == bindparam("case"))
                .values({proc_col: proc_col + bindparam("proc")}),
                params,
            )
            query = session.query(CaseForms).filter(case_col.in_(cases))
            case_forms = {cf.case_id: cf for cf in query}

            def make_result(case_id):
                case = case_forms.get(case_id)
                if case is None:
                    return (case_id, None, None)
                return (case_id, case.total_forms, case.processed_forms)

            return [make_result(case_id) for case_id in cases]

    def iter_cases_with_unprocessed_forms(self):
        query = self.Session().query(
            CaseForms.case_id,
            CaseForms.total_forms,
        ).filter(CaseForms.total_forms > CaseForms.processed_forms)
        for case_id, total_forms in iter_large(query, CaseForms.case_id):
            yield case_id, total_forms

    def get_forms_count(self, case_id):
        with self.session() as session:
            query = session.query(CaseForms.total_forms).filter_by(case_id=case_id)
            return query.scalar() or 0

    def add_problem_form(self, form_id):
        """Add form to be migrated with "unprocessed" forms

        A "problem" form is an error form with normal doctype (XFormInstance)
        """
        with self.session() as session:
            session.add(ProblemForm(id=form_id))

    def iter_problem_forms(self):
        query = self.Session().query(ProblemForm.id)
        for form_id, in iter_large(query, ProblemForm.id):
            yield form_id

    def add_no_action_case_form(self, form_id):
        try:
            with self.session() as session:
                session.add(NoActionCaseForm(id=form_id))
        except IntegrityError:
            pass
        else:
            self.get_no_action_case_forms.reset_cache(self)

    @memoized
    def get_no_action_case_forms(self):
        """Get the set of form ids that touch cases without actions"""
        return {x for x, in self.Session().query(NoActionCaseForm.id)}

    def set_resume_state(self, key, value):
        resume_key = "resume-{}".format(key)
        self._upsert(KeyValue, KeyValue.key, resume_key, json.dumps(value))

    @contextmanager
    def pop_resume_state(self, key, default):
        resume_key = "resume-{}".format(key)
        with self.session() as session:
            kv = self._get_kv(resume_key, session)
            if kv is None:
                self._set_kv(resume_key, RESUME_NOT_ALLOWED, session)
                yield default
            elif self.is_rebuild:
                yield default
            elif kv.value == RESUME_NOT_ALLOWED:
                raise ResumeError("previous session did not save resume state")
            else:
                yield json.loads(kv.value)
                kv.value = RESUME_NOT_ALLOWED

    def _get_kv(self, key, session):
        return session.query(KeyValue).get(key)

    def _set_kv(self, key, value, session=None):
        with self.session(session) as session:
            session.add(KeyValue(key=key, value=value))

    def _upsert(self, model, key_field, key, value, incr=False):
        with self.session() as session:
            updated = (
                session.query(model)
                .filter(key_field == key)
                .update(
                    {model.value: (model.value + value) if incr else value},
                    synchronize_session=False,
                )
            )
            if not updated:
                obj = model(value=value)
                key_field.__set__(obj, key)
                session.add(obj)
            else:
                assert updated == 1, (key, updated)

    def add_missing_docs(self, kind, doc_ids):
        with self.session() as session:
            session.bulk_save_objects([
                MissingDoc(kind=kind, doc_id=doc_id)
                for doc_id in doc_ids
            ])

    def save_form_diffs(self, couch_json, sql_json):
        diffs = json_diff(couch_json, sql_json, track_list_indices=False)
        diffs = filter_form_diffs(couch_json, sql_json, diffs)
        if diffs:
            self.add_diffs(couch_json["doc_type"], couch_json["_id"], diffs)

    def replace_case_diffs(self, kind, case_id, diffs):
        from .couchsqlmigration import CASE_DOC_TYPES
        assert kind in CASE_DOC_TYPES, kind
        with self.session() as session:
            (
                session.query(Diff)
                .filter(or_(
                    and_(Diff.kind == "CommCareCase", Diff.doc_id == case_id),
                    and_(Diff.kind == "stock state", Diff.doc_id.startswith(case_id + "/")),
                ))
                .delete(synchronize_session=False)
            )
        if diffs:
            self.add_diffs(kind, case_id, diffs)

    def increment_counter(self, kind, value):
        self._upsert(DocCount, DocCount.kind, kind, value, incr=True)

    def get_doc_counts(self):
        """Returns a dict of counts by kind

        Values are `Counts` objects having `total` and `missing`
        fields:

        - total: number of items counted with `increment_counter`.
        - missing: count of ids added with `add_missing_docs`.
        """
        with self.session() as session:
            totals = {dc.kind: dc.value for dc in session.query(DocCount)}
            missing = {row[0]: row[1] for row in session.query(
                MissingDoc.kind,
                func.count(MissingDoc.doc_id),
            ).group_by(MissingDoc.kind).all()}
        return {kind: Counts(
            total=totals.get(kind, 0),
            missing=missing.get(kind, 0),
        ) for kind in set(missing) | set(totals)}

    def has_doc_counts(self):
        if not os.path.exists(self.db_filepath):
            return False
        return self.engine.dialect.has_table(self.engine, "doc_count")

    def get_missing_doc_ids(self, doc_type):
        return {
            missing.doc_id for missing in self.Session()
            .query(MissingDoc.doc_id)
            .filter(MissingDoc.kind == doc_type)
        }

    def clone_casediff_data_from(self, casediff_state_path):
        """Copy casediff state into this state db

        model analysis
        - CaseForms - casediff r/w
        - Diff - casediff w (case and stock kinds), main r/w
        - KeyValue - casediff r/w, main r/w (different keys)
        - DocCount - casediff w, main r
        - MissingDoc - casediff w, main r
        - NoActionCaseForm - main r/w
        - ProblemForm - main r/w
        """
        def quote(value):
            assert isinstance(value, str) and "'" not in value, repr(value)
            return f"'{value}'"

        def quotelist(values):
            return f"({', '.join(quote(v) for v in values)})"

        def is_id(column):
            return column.key == "id" and isinstance(column.type, Integer)

        def copy(model, session, where_expr=None):
            log.info("copying casediff data: %s", model.__name__)
            where = f"WHERE {where_expr}" if where_expr else ""
            fields = ", ".join(c.key for c in model.__table__.columns if not is_id(c))
            session.execute(f"DELETE FROM main.{model.__tablename__} {where}")
            session.execute(f"""
                INSERT INTO main.{model.__tablename__} ({fields})
                SELECT {fields} FROM cddb.{model.__tablename__} {where}
            """)

        log.info("checking casediff data preconditions...")
        casediff_db = type(self).open(casediff_state_path)
        with casediff_db.session() as cddb:
            expect_casediff_kinds = {
                "CommCareCase",
                "CommCareCase-Deleted",
                "stock state",
            }
            casediff_kinds = {k for k, in cddb.query(Diff.kind).distinct()}
            assert not casediff_kinds - expect_casediff_kinds, casediff_kinds

            resume_keys = [
                key for key, in cddb.query(KeyValue.key)
                .filter(KeyValue.key.startswith("resume-"))
            ]
            assert all("Case" in key for key in resume_keys), resume_keys

            count_kinds = [k for k, in cddb.query(DocCount.kind).distinct()]
            assert all("CommCareCase" in k for k in count_kinds), count_kinds

            missing_kinds = [m for m, in cddb.query(MissingDoc.kind).distinct()]
            assert all("CommCareCase" in k for k in missing_kinds), missing_kinds
        casediff_db.close()

        with self.session() as session:
            session.execute(f"ATTACH DATABASE {quote(casediff_state_path)} AS cddb")
            copy(CaseForms, session)
            copy(Diff, session, f"kind IN {quotelist(expect_casediff_kinds)}")
            copy(KeyValue, session, f"key IN {quotelist(resume_keys)}")
            copy(DocCount, session)
            copy(MissingDoc, session)


class ResumeError(Exception):
    pass


RESUME_NOT_ALLOWED = "RESUME_NOT_ALLOWED"


class CaseForms(Base):
    __tablename__ = "caseforms"

    case_id = Column(String(50), nullable=False, primary_key=True)
    total_forms = Column(Integer, nullable=False)
    processed_forms = Column(Integer, nullable=False, default=0)


class DocCount(Base):
    __tablename__ = 'doc_count'

    kind = Column(String(50), primary_key=True)
    value = Column(Integer, nullable=False)


class KeyValue(Base):
    __tablename__ = "keyvalue"

    key = Column(String(50), nullable=False, primary_key=True)
    value = Column(Text(), nullable=False)


class MissingDoc(Base):
    __tablename__ = 'missing_doc'

    id = Column(Integer, primary_key=True)
    kind = Column(String(50), nullable=False)
    doc_id = Column(String(50), nullable=False)


class NoActionCaseForm(Base):
    __tablename__ = "noactioncaseform"

    id = Column(String(50), nullable=False, primary_key=True)


class ProblemForm(Base):
    __tablename__ = "problemform"

    id = Column(String(50), nullable=False, primary_key=True)


diff_doc_id_idx = Index("diff_doc_id_idx", Diff.doc_id)


Counts = namedtuple('Counts', 'total missing')


def iter_large(query, pk_attr, maxrq=1000):
    """Specialized windowed query generator using WHERE/LIMIT

    Iterate over a dataset that is too large to fetch at once. Results
    are ordered by `pk_attr`.

    Adapted from https://github.com/sqlalchemy/sqlalchemy/wiki/WindowedRangeQuery
    """
    first_id = None
    while True:
        qry = query
        if first_id is not None:
            qry = query.filter(pk_attr > first_id)
        rec = None
        for rec in qry.order_by(pk_attr).limit(maxrq):
            yield rec
        if rec is None:
            break
        first_id = getattr(rec, pk_attr.name)

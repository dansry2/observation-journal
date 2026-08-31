from app.database import JournalSessionLocal, journal_engine, JournalBase
from app.models import *

JournalBase.metadata.create_all(bind=journal_engine)
print("База создана (без справочников)")

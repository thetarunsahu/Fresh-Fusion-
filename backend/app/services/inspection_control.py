from ..models import FruitSample, InspectionControl

def active_sample(db):
    control = db.get(InspectionControl, 1)
    if control:
        return db.query(FruitSample).filter_by(sample_id=control.sample_id).first()
    # Compatibility for databases created before explicit capture selection.
    return db.query(FruitSample).order_by(FruitSample.created_at.desc()).first()

def set_active(db, sample):
    control = db.get(InspectionControl, 1)
    if control is None:
        db.add(InspectionControl(id=1, sample_id=sample.sample_id))
    else:
        control.sample_id = sample.sample_id
    db.commit()

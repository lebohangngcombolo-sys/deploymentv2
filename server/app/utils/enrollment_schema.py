from marshmallow import Schema, fields

class EnrollmentSchema(Schema):
    full_name = fields.String(required=False)
    phone = fields.String(required=False)
    dob = fields.String(required=False)
    address = fields.String(required=False)
    gender = fields.String(required=False)
    bio = fields.String(required=False)
    title = fields.String(required=False)
    location = fields.String(required=False)
    nationality = fields.String(required=False)
    id_number = fields.String(required=False)
    linkedin = fields.String(required=False)
    github = fields.String(required=False)
    cv_url = fields.String(required=False)
    portfolio = fields.String(required=False)
    cover_letter = fields.String(required=False)
    profile_picture = fields.String(required=False)

    # JSON structured fields
    education = fields.List(fields.Dict(), required=False)
    skills = fields.List(fields.Raw(), required=False)
    work_experience = fields.List(fields.Dict(), required=False)
    certifications = fields.List(fields.Dict(), required=False)
    languages = fields.List(fields.Dict(), required=False)
    documents = fields.List(fields.Dict(), required=False)
    profile = fields.Dict(required=False)

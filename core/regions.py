REGION_CHOICES = (
    ('US', 'United States'),
    ('CA', 'Canada'),
    ('GB', 'United Kingdom'),
    ('AU', 'Australia'),
    ('DE', 'Germany'),
    ('FR', 'France'),
    ('ES', 'Spain'),
    ('IT', 'Italy'),
    ('JP', 'Japan'),
)

REGION_CODES = {code for code, _label in REGION_CHOICES}

import re
from django.db import models
from django.utils.text import slugify
from recruiters.models import Company, RecruiterProfile


class Skill(models.Model):
    CATEGORY_CHOICES = (
        ('BACKEND', 'Backend Development'),
        ('FRONTEND', 'Frontend Development'),
        ('CLOUD', 'Cloud & DevOps'),
        ('AI_ML', 'AI & Machine Learning'),
        ('DATABASE', 'Database & SQL'),
        ('SYSTEMS', 'Embedded & Systems'),
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='BACKEND')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('FULL_TIME', 'Full-Time Employment'),
        ('CONTRACT', 'Contractual'),
        ('GRADUATE', 'Graduate Engineer Trainee (GET)'),
    )
    WORKPLACE_CHOICES = (
        ('REMOTE', 'Remote'),
        ('HYBRID', 'Hybrid'),
        ('ON_SITE', 'On-Site'),
    )

    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='posted_jobs')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    job_type = models.CharField(max_length=30, choices=JOB_TYPE_CHOICES, default='FULL_TIME')
    workplace_type = models.CharField(max_length=20, choices=WORKPLACE_CHOICES, default='HYBRID')
    location = models.CharField(max_length=150, default='Bengaluru, India')
    salary_range = models.CharField(max_length=100, default='₹8,00,000 - ₹14,00,000 P.A.')
    description = models.TextField()
    responsibilities = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    required_skills = models.ManyToManyField(Skill, related_name='jobs', blank=True)
    eligible_branches = models.CharField(max_length=200, default='CSE, ECE, IT', help_text="Comma-separated branches")
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=7.00)
    openings = models.PositiveIntegerField(default=3)
    deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # External import & synchronization tracking
    is_external_import = models.BooleanField(default=False, help_text="True if imported from Greenhouse or public board")
    external_source = models.CharField(max_length=50, blank=True, default='')
    external_id = models.CharField(max_length=100, blank=True, default='')
    external_apply_url = models.URLField(max_length=500, blank=True, default='')
    external_department = models.CharField(max_length=150, blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        source_tag = f" [{self.external_source}]" if self.is_external_import else ""
        return f"{self.title} at {self.company.name}{source_tag}"

    @property
    def seniority_level(self):
        t = self.title.lower()
        if re.search(r'\b(vp|vice president|c-level|chief|cto|cfo|cio)\b', t):
            return 'Executive / VP'
        if re.search(r'\b(director|head of)\b', t):
            return 'Director'
        if re.search(r'\b(manager\s+ii|manager\s+2)\b', t):
            return 'Manager II'
        if re.search(r'\b(manager\s+i|manager\s+1|manager)\b', t):
            return 'Management'
        if re.search(r'\b(principal)\b', t):
            return 'Principal'
        if re.search(r'\b(staff)\b', t):
            return 'Staff Level'
        if re.search(r'\b(lead)\b', t):
            return 'Lead'
        if re.search(r'\b(senior|sr\.?)\b', t):
            return 'Senior'
        if re.search(r'(\b3\b|\biii\b|level\s*3)', t):
            return 'Level 3'
        if re.search(r'(\b2\b|\bii\b|level\s*2)', t):
            return 'Level 2'
        if re.search(r'(\b1\b|\bi\b|level\s*1)', t):
            return 'Level 1'
        if re.search(r'\b(entry[\s-]level|associate|junior|jr\.?)\b', t):
            return 'Entry Level'
        if re.search(r'\b(intern|internship|trainee|apprentice)\b', t):
            return 'Intern / Trainee'
        return 'Mid / Professional'

    @property
    def clean_title(self):
        title = self.title.strip()
        m = re.match(r'^(.*?),\s*(Premier|Enterprise|Commercial|Public Sector|Core|Cloud|Security)\s*-\s*(.*)$', title, re.I)
        if m:
            return m.group(1).strip()
        if ' - ' in title:
            parts = [p.strip() for p in title.split(' - ') if p.strip()]
            if len(parts) >= 2:
                last = parts[-1].lower()
                loc_lower = (self.location or '').lower()
                if last in loc_lower or any(c in last for c in ['sao paulo', 'tokyo', 'emea', 'apac', 'london', 'san francisco', 'remote']):
                    return ' - '.join(parts[:-1])
        return title

    @property
    def display_service_category(self):
        title = self.title.strip()
        m = re.match(r'^(.*?),\s*(Premier|Enterprise|Commercial|Public Sector|Core|Cloud|Security)\s*-\s*(.*)$', title, re.I)
        if m:
            cat = m.group(2).strip()
            dept = self.external_department or ''
            if 'support' in dept.lower() or 'support' in title.lower():
                return f"{cat} Support"
            return cat
        if self.external_department:
            return self.external_department
        return 'Engineering & Technology'

    @property
    def display_salary(self):
        sal = self.salary_range or ''
        if 'Engineering Band' in sal:
            dept = (self.external_department or '').lower()
            title = self.title.lower()
            if any(w in dept or w in title for w in ['finance', 'investor', 'accounting']):
                return 'Competitive Finance Band'
            elif any(w in dept or w in title for w in ['sales', 'account executive', 'account manager']):
                return 'Competitive Sales & Commission'
            elif any(w in dept or w in title for w in ['people', 'hr', 'recruiting', 'talent']):
                return 'Competitive HR / Talent Band'
            elif any(w in dept or w in title for w in ['legal', 'compliance']):
                return 'Competitive Legal Band'
            elif any(w in dept or w in title for w in ['marketing', 'communications']):
                return 'Competitive Marketing Band'
            elif any(w in title for w in ['vp', 'vice president', 'director']):
                return 'Executive Compensation Package'
            elif not any(w in dept or w in title for w in ['eng', 'software', 'dev', 'tech', 'data', 'security', 'systems', 'support']):
                return 'Market Competitive'
        return sal or 'Market Competitive'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.company.name}-{self.title}") or 'job'
            self.slug = base
            count = 1
            while Job.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base}-{count}"
                count += 1
        super().save(*args, **kwargs)


class Internship(models.Model):
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='posted_internships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='internships')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    duration = models.CharField(max_length=50, default='6 Months')
    stipend = models.CharField(max_length=100, default='₹35,000 / Month')
    location = models.CharField(max_length=150, default='Hybrid / Remote')
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, related_name='internships', blank=True)
    eligible_branches = models.CharField(max_length=200, default='CSE, ECE, EE, IT')
    deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # External import & synchronization tracking
    is_external_import = models.BooleanField(default=False, help_text="True if imported from Greenhouse or public board")
    external_source = models.CharField(max_length=50, blank=True, default='')
    external_id = models.CharField(max_length=100, blank=True, default='')
    external_apply_url = models.URLField(max_length=500, blank=True, default='')
    external_department = models.CharField(max_length=150, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        source_tag = f" [{self.external_source}]" if self.is_external_import else ""
        return f"{self.title} (Internship) at {self.company.name}{source_tag}"

    @property
    def seniority_level(self):
        return 'Intern / Trainee'

    @property
    def clean_title(self):
        title = self.title.strip()
        m = re.match(r'^(.*?),\s*(Premier|Enterprise|Commercial|Public Sector|Core|Cloud|Security)\s*-\s*(.*)$', title, re.I)
        if m:
            return m.group(1).strip()
        if ' - ' in title:
            parts = [p.strip() for p in title.split(' - ') if p.strip()]
            if len(parts) >= 2:
                last = parts[-1].lower()
                loc_lower = (self.location or '').lower()
                if last in loc_lower or any(c in last for c in ['sao paulo', 'tokyo', 'emea', 'apac', 'london', 'san francisco', 'remote']):
                    return ' - '.join(parts[:-1])
        return title

    @property
    def display_service_category(self):
        title = self.title.strip()
        m = re.match(r'^(.*?),\s*(Premier|Enterprise|Commercial|Public Sector|Core|Cloud|Security)\s*-\s*(.*)$', title, re.I)
        if m:
            cat = m.group(2).strip()
            dept = self.external_department or ''
            if 'support' in dept.lower() or 'support' in title.lower():
                return f"{cat} Support"
            return cat
        if self.external_department:
            return self.external_department
        return 'Engineering Internship'

    @property
    def display_salary(self):
        return self.stipend or 'Competitive Stipend'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"intern-{self.company.name}-{self.title}") or 'intern'
            self.slug = base
            count = 1
            while Internship.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base}-{count}"
                count += 1
        super().save(*args, **kwargs)


class ExternalListing(models.Model):
    """
    Stores raw external listing metadata, payload, and mapping to Job or Internship.
    Guarantees idempotency and duplicate prevention across repeated synchronizations.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='external_listings')
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='external_listings')
    source_provider = models.CharField(max_length=50, default='GREENHOUSE')
    external_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=150, blank=True)
    location_raw = models.CharField(max_length=255, blank=True)
    apply_url = models.URLField(max_length=500, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    job = models.OneToOneField(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='external_record')
    internship = models.OneToOneField(Internship, on_delete=models.SET_NULL, null=True, blank=True, related_name='external_record')
    is_internship = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    first_imported_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['source_provider', 'external_id'], name='unique_external_provider_listing')
        ]
        ordering = ['-last_synced_at']

    def __str__(self):
        role_type = "Internship" if self.is_internship else "Job"
        return f"[{self.source_provider}] {self.title} ({role_type}) - {self.company.name}"

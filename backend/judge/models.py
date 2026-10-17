from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Organization(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    short_name = models.CharField(max_length=32)
    about = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    logo = models.TextField(blank=True, default='/frontend/assets/icons/org-default.svg')
    cover = models.TextField(blank=True, default='/frontend/assets/images/codepro-cover.jpg')
    website = models.CharField(max_length=255, blank=True, default='https://codeprooj.com')
    owner_id = models.IntegerField(default=1)
    verified = models.BooleanField(default=False)
    is_open = models.BooleanField(default=True)
    member_count = models.IntegerField(default=0)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    key = models.CharField(max_length=20, unique=True) # CPP17, PY3, JAVA17, RUST
    name = models.CharField(max_length=50) # C++17 (GCC 11.2)
    short_name = models.CharField(max_length=20) # C++17
    common_name = models.CharField(max_length=20) # C++
    ace_mode_name = models.CharField(max_length=30, default='c_cpp')
    pygments_style = models.CharField(max_length=30, default='cpp')
    template = models.TextField(blank=True, default='')
    info = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=32, default='user') # admin, teacher, setter, user
    about = models.TextField(blank=True, default='')
    timezone = models.CharField(max_length=50, default='Asia/Ho_Chi_Minh')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    points = models.FloatField(default=0.0)
    performance_points = models.FloatField(default=0.0)
    problem_count = models.IntegerField(default=0)
    rating = models.IntegerField(null=True, blank=True, default=0)
    display_rank = models.CharField(max_length=50, default='Unrated')
    is_verified = models.BooleanField(default=False)
    organizations = models.ManyToManyField(Organization, blank=True, related_name='members')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_teacher(self):
        return self.role == 'teacher' or self.user.groups.filter(name='teacher').exists()

    def can_create_organization(self):
        return bool(
            self.user.is_active and
            (self.user.is_superuser or self.user.is_staff or self.is_teacher())
        )

    def __str__(self):
        return self.user.username

    def update_rating_rank(self):
        r = self.rating or 0
        if r == 0: self.display_rank = 'Unrated'
        elif r >= 3000: self.display_rank = 'Legendary Grandmaster'
        elif r >= 2400: self.display_rank = 'Grandmaster'
        elif r >= 2100: self.display_rank = 'Master'
        elif r >= 1900: self.display_rank = 'Candidate Master'
        elif r >= 1600: self.display_rank = 'Expert'
        elif r >= 1400: self.display_rank = 'Specialist'
        elif r >= 1200: self.display_rank = 'Pupil'
        else: self.display_rank = 'Newbie'
        self.save(update_fields=['display_rank'])

class ProblemType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name

class ProblemGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name

class Problem(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=128)
    description = models.TextField(help_text='Markdown/KaTeX problem statement')
    time_limit = models.FloatField(default=1.0)
    memory_limit = models.IntegerField(default=262144) # KB
    points = models.FloatField(default=100.0)
    partial = models.BooleanField(default=False)
    short_circuit = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    is_organization_private = models.BooleanField(default=False)
    organizations = models.ManyToManyField(Organization, blank=True)
    types = models.ManyToManyField(ProblemType, blank=True, related_name='problems')
    group = models.ForeignKey(ProblemGroup, on_delete=models.SET_NULL, null=True, blank=True)
    authors = models.ManyToManyField(Profile, blank=True, related_name='authored_problems')
    bendo_data = models.JSONField(default=dict, blank=True)
    is_manually_managed = models.BooleanField(default=False)
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('published', 'Published')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    difficulty = models.CharField(max_length=20, default='medium', blank=True)
    date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Contest(models.Model):
    DISPLAY_TARGET_CHOICES = (
        ('both', 'Web và client'),
        ('web', 'Chỉ web'),
        ('client', 'Chỉ client'),
    )
    FORMAT_CHOICES = (
        ('icpc', 'ICPC Format'),
        ('ioi', 'IOI Partial Format'),
        ('atcoder', 'AtCoder Format'),
    )
    key = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default='')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    time_limit = models.IntegerField(help_text='Duration in seconds', default=7200)
    is_rated = models.BooleanField(default=True)
    rate_all = models.BooleanField(default=False)
    format_name = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='icpc')
    is_visible = models.BooleanField(default=True)
    display_target = models.CharField(max_length=6, choices=DISPLAY_TARGET_CHOICES, default='both')
    hide_scoreboard = models.BooleanField(default=False)
    scoreboard_freeze = models.DateTimeField(null=True, blank=True)
    access_code = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ContestProblem(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='contest_problems')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    points = models.FloatField(default=100.0)
    partial = models.BooleanField(default=False)
    order = models.IntegerField(default=1)
    output_prefix = models.CharField(max_length=10, blank=True, default='A')

    class Meta:
        unique_together = ('contest', 'problem')
        ordering = ['order']

    def __str__(self):
        return f"{self.contest.key} - {self.output_prefix}: {self.problem.code}"

class ContestParticipation(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='contest_participations')
    real_start = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0.0)
    cumulative_time = models.IntegerField(default=0) # Penalty in seconds
    tiebreaker = models.FloatField(default=0.0)
    is_disqualified = models.BooleanField(default=False)
    format_data = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return f"{self.user.user.username} in {self.contest.key}"

class Judge(models.Model):
    name = models.CharField(max_length=50, unique=True)
    auth_key = models.CharField(max_length=128)
    is_blocked = models.BooleanField(default=False)
    online = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    ping = models.FloatField(null=True, blank=True)
    load = models.FloatField(default=0.0)
    last_seen = models.DateTimeField(null=True, blank=True)
    runtime_versions = models.JSONField(default=dict, blank=True)
    languages = models.ManyToManyField(Language, blank=True)

    def __str__(self):
        return f"Judge: {self.name} ({'Online' if self.online else 'Offline'})"

class Submission(models.Model):
    RESULT_CHOICES = (
        ('AC', 'Accepted'),
        ('WA', 'Wrong Answer'),
        ('TLE', 'Time Limit Exceeded'),
        ('MLE', 'Memory Limit Exceeded'),
        ('OLE', 'Output Limit Exceeded'),
        ('RTE', 'Runtime Error'),
        ('IR', 'Invalid Return'),
        ('CE', 'Compilation Error'),
        ('SE', 'System Error'),
        ('IE', 'Internal Error'),
        ('AB', 'Aborted'),
        ('SC', 'Short Circuited'),
    )
    STATUS_CHOICES = (
        ('QU', 'Queued'),
        ('P', 'Processing'),
        ('G', 'Grading'),
        ('D', 'Done'),
    )

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='submissions')
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    time = models.FloatField(null=True, blank=True) # Seconds
    memory = models.FloatField(null=True, blank=True) # Kilobytes
    points = models.FloatField(null=True, blank=True)
    result = models.CharField(max_length=5, choices=RESULT_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='QU')
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    source = models.TextField()
    error = models.TextField(blank=True, default='')
    is_rejudged = models.BooleanField(default=False)
    contest = models.ForeignKey(Contest, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Sub #{self.id} - {self.user.user.username} on {self.problem.code} ({self.result})"

class SubmissionTestCase(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='test_cases')
    case = models.IntegerField()
    status = models.CharField(max_length=5, choices=Submission.RESULT_CHOICES)
    time = models.FloatField(default=0.0)
    memory = models.FloatField(default=0.0)
    points = models.FloatField(default=0.0)
    total_points = models.FloatField(default=10.0)
    feedback = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['case']

    def __str__(self):
        return f"Sub #{self.submission.id} Case #{self.case}: {self.status}"


class JudgeWorker(models.Model):
    name = models.CharField(max_length=80, unique=True)
    hostname = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=16, default='OFFLINE')
    cpu_count = models.PositiveIntegerField(default=0)
    memory_limit = models.PositiveIntegerField(default=0, help_text='MB')
    supported_languages = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    maintenance = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'judge_workers'


class JudgeJob(models.Model):
    remote_id = models.CharField(max_length=80, unique=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='judge_jobs')
    worker = models.ForeignKey(JudgeWorker, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.IntegerField(default=10)
    status = models.CharField(max_length=16, default='WAITING')
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'judge_jobs'
        indexes = [models.Index(fields=['status', 'created_at'])]


class JudgeResult(models.Model):
    job = models.OneToOneField(JudgeJob, on_delete=models.CASCADE, related_name='judge_result')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, null=True, blank=True)
    worker = models.ForeignKey(JudgeWorker, on_delete=models.SET_NULL, null=True, blank=True)
    verdict = models.CharField(max_length=12)
    score = models.FloatField(default=0)
    execution_time = models.FloatField(default=0, help_text='ms')
    memory_used = models.FloatField(default=0, help_text='KB')
    output_size = models.PositiveIntegerField(default=0)
    compile_time = models.FloatField(default=0, help_text='ms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'judge_results'


class JudgeLog(models.Model):
    worker = models.ForeignKey(JudgeWorker, on_delete=models.SET_NULL, null=True, blank=True)
    job = models.ForeignKey(JudgeJob, on_delete=models.SET_NULL, null=True, blank=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    level = models.CharField(max_length=12, default='INFO')
    action = models.CharField(max_length=64, blank=True)
    message = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'judge_logs'
        ordering = ['-created_at']

class RatingHistory(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='ratings')
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    rating = models.IntegerField()
    volatility = models.IntegerField(default=0)
    ranking = models.IntegerField(default=1)
    last_rated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} - {self.contest.key}: {self.rating}"

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    body = models.TextField()
    publish_on = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    body = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    page = models.CharField(max_length=100) # e.g., "p:KNAPSACK"

    def __str__(self):
        return f"Comment by {self.author.user.username} on {self.page}"

class Clarification(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='clarifications')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, null=True, blank=True, related_name='clarifications')
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=True, blank=True, related_name='clarifications')
    question = models.TextField()
    answer = models.TextField(blank=True, default='')
    is_public = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    answered_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_clarifications')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        target = self.problem.code if self.problem else (self.contest.key if self.contest else 'General')
        return f"Clarification on {target} by {self.user.user.username}"


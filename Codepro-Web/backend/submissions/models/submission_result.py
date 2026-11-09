class SubmissionResult:
    VERDICTS = {
        'AC': 'Accepted',
        'WA': 'Wrong Answer',
        'TLE': 'Time Limit Exceeded',
        'MLE': 'Memory Limit Exceeded',
        'RE': 'Runtime Error',
        'RTE': 'Runtime Error',
        'CE': 'Compilation Error',
        'OLE': 'Output Limit Exceeded',
        'IE': 'Internal Error',
        'QU': 'Queued',
        'P': 'Processing',
        'G': 'Grading',
        'D': 'Done'
    }

    STATUSES = ['QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING', 'FINISHED']

    @classmethod
    def get_verdict_name(cls, code):
        return cls.VERDICTS.get(code, code)

import math
from datetime import datetime

class ScoreCalculator:
    """
    Score calculation for competitive programming contests.
    Supports ICPC (problems solved + penalty in minutes)
    and IOI (sum of partial/maximum points per problem).
    """

    @staticmethod
    def calculate_icpc(submissions, contest_start_time, penalty_per_wa_minutes=20):
        """
        submissions: list of dict or objects with:
          - problem_id (or problem_code)
          - result: 'AC', 'WA', 'TLE', etc.
          - date (datetime)
        contest_start_time: datetime
        Returns:
          {
            'solved': int,
            'total_penalty': int,
            'problems': {
                'A': {
                    'status': 'AC' | 'WA' | 'PENDING' | 'NONE',
                    'tries': int, # total submissions made
                    'penalty': int, # penalty minutes for this problem if AC
                    'time': int, # minutes from start to AC
                    'first_ac': bool,
                    'score': int (1 or 0)
                }
            }
          }
        """
        problem_map = {}
        solved_count = 0
        total_penalty = 0

        # Sort submissions chronologically
        sorted_subs = sorted(submissions, key=lambda s: getattr(s, 'date', None) or s.get('date'))

        for sub in sorted_subs:
            prob = getattr(sub, 'problem_code', None) or (getattr(sub, 'problem', None) and getattr(sub.problem, 'code', str(sub.problem))) or sub.get('problem_code', 'unknown')
            result = getattr(sub, 'result', None) or sub.get('result', '')
            sub_date = getattr(sub, 'date', None) or sub.get('date')

            if prob not in problem_map:
                problem_map[prob] = {
                    'status': 'NONE',
                    'tries': 0,
                    'penalty': 0,
                    'time': 0,
                    'first_ac': False,
                    'score': 0,
                    'is_solved': False
                }

            prob_info = problem_map[prob]
            if prob_info['is_solved']:
                # Any submissions after AC do not count towards penalty in ICPC
                continue

            prob_info['tries'] += 1

            if result == 'AC':
                prob_info['is_solved'] = True
                prob_info['status'] = 'AC'
                prob_info['score'] = 100 # or 1

                # Calculate minutes from contest start
                if contest_start_time and sub_date:
                    delta = sub_date - contest_start_time
                    minutes = max(0, int(delta.total_seconds() // 60))
                else:
                    minutes = 0

                prob_info['time'] = minutes
                # ICPC penalty: AC time (in minutes) + 20 minutes for each failed attempt prior to AC
                problem_penalty = minutes + ((prob_info['tries'] - 1) * penalty_per_wa_minutes)
                prob_info['penalty'] = problem_penalty
                solved_count += 1
                total_penalty += problem_penalty
            else:
                prob_info['status'] = 'WA'

        return {
            'solved': solved_count,
            'total_penalty': total_penalty,
            'problems': problem_map
        }

    @staticmethod
    def calculate_ioi(submissions):
        """
        Calculates IOI format score: maximum points obtained for each problem.
        """
        problem_map = {}
        total_score = 0.0

        for sub in submissions:
            prob = getattr(sub, 'problem_code', None) or (getattr(sub, 'problem', None) and getattr(sub.problem, 'code', str(sub.problem))) or sub.get('problem_code', 'unknown')
            points = float(getattr(sub, 'points', 0.0) or sub.get('points', 0.0) or 0.0)
            result = getattr(sub, 'result', None) or sub.get('result', '')

            if prob not in problem_map:
                problem_map[prob] = {
                    'status': 'NONE',
                    'tries': 0,
                    'score': 0.0,
                    'is_solved': False
                }

            p = problem_map[prob]
            p['tries'] += 1
            if points > p['score']:
                p['score'] = points
            if result == 'AC' or points >= 100.0:
                p['is_solved'] = True
                p['status'] = 'AC'
            elif p['score'] > 0:
                p['status'] = 'PARTIAL'
            else:
                p['status'] = 'WA'

        total_score = sum(item['score'] for item in problem_map.values())
        solved_count = sum(1 for item in problem_map.values() if item['is_solved'])

        return {
            'solved': solved_count,
            'score': round(total_score, 2),
            'problems': problem_map
        }

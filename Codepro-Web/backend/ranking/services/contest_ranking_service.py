from datetime import datetime
from django.utils import timezone
from ..models.contest_ranking import ContestRanking
from ..calculators.score import ScoreCalculator
from ..calculators.rank import RankCalculator
from backend.judge.models import Contest, ContestProblem, Submission, ContestParticipation

class ContestRankingService:
    @staticmethod
    def get_scoreboard(contest_identifier, live=True):
        """
        Retrieves or calculates the scoreboard for a contest.
        contest_identifier: ID or key (e.g. 'codeprooj-cup-2026-r1' or 1)
        """
        contest = None
        if isinstance(contest_identifier, int) or (isinstance(contest_identifier, str) and contest_identifier.isdigit()):
            contest = Contest.objects.filter(id=int(contest_identifier)).first()
        if not contest:
            contest = Contest.objects.filter(key=str(contest_identifier)).first()

        if not contest:
            return {'error': 'Contest not found', 'rows': [], 'problems': []}

        contest_problems = ContestProblem.objects.filter(contest=contest).select_related('problem').order_by('order')
        problems_list = []
        prob_codes = []
        for cp in contest_problems:
            prefix = cp.output_prefix or chr(65 + cp.order - 1)
            problems_list.append({
                'prefix': prefix,
                'code': cp.problem.code,
                'name': cp.problem.name,
                'points': cp.points,
            })
            prob_codes.append(cp.problem.code)

        # Check if contest rankings are already computed
        cached_rankings = ContestRanking.objects.filter(contest=contest).select_related('user').order_by('rank')

        # If cached and live is False, return cached
        if cached_rankings.exists() and not live:
            rows = []
            for cr in cached_rankings:
                rows.append({
                    'rank': cr.rank,
                    'user_id': cr.user.id,
                    'username': cr.user.username,
                    'solved': cr.solved,
                    'penalty': cr.penalty,
                    'score': cr.score,
                    'rating_change': cr.rating_change,
                    'problem_results': cr.problem_details,
                })
            return {
                'contest': {
                    'id': contest.id,
                    'key': contest.key,
                    'name': contest.name,
                    'format': contest.format_name,
                    'start_time': contest.start_time.isoformat() if contest.start_time else None,
                    'end_time': contest.end_time.isoformat() if contest.end_time else None,
                    'is_frozen': False,
                },
                'problems': problems_list,
                'rows': rows
            }

        # Otherwise calculate from submissions live
        submissions = Submission.objects.filter(contest=contest).select_related('user__user', 'problem').order_by('date')
        
        # Group submissions by user
        user_subs = {}
        for sub in submissions:
            username = sub.user.user.username
            if username not in user_subs:
                user_subs[username] = {
                    'user': sub.user.user,
                    'subs': []
                }
            user_subs[username]['subs'].append({
                'problem_code': sub.problem.code,
                'result': sub.result,
                'points': sub.points,
                'date': sub.date
            })

        # Calculate scores per participant
        raw_participants = []
        for username, data in user_subs.items():
            calc = ScoreCalculator.calculate_icpc(data['subs'], contest.start_time)
            raw_participants.append({
                'user': data['user'],
                'username': username,
                'solved': calc['solved'],
                'penalty': calc['total_penalty'],
                'problems': calc['problems'],
                'last_ac_time': max([p['time'] for p in calc['problems'].values() if p.get('is_solved')] or [0])
            })

        # Assign ranks
        ranked = RankCalculator.rank_icpc(raw_participants)

        # Detect first AC for each problem across the contest
        for p_code in prob_codes:
            earliest_time = None
            first_user = None
            for p in ranked:
                prob_data = p['problems'].get(p_code)
                if prob_data and prob_data.get('is_solved'):
                    ac_time = prob_data.get('time', 999999)
                    if earliest_time is None or ac_time < earliest_time:
                        earliest_time = ac_time
                        first_user = p

            if first_user and p_code in first_user['problems']:
                first_user['problems'][p_code]['first_ac'] = True

        # Build output rows and persist/update in DB
        rows = []
        for r in ranked:
            # Map problems by prefix
            prob_map_by_prefix = {}
            for cp in problems_list:
                code = cp['code']
                prefix = cp['prefix']
                if code in r['problems']:
                    prob_map_by_prefix[prefix] = r['problems'][code]
                else:
                    prob_map_by_prefix[prefix] = {'status': 'NONE', 'tries': 0, 'score': 0, 'time': 0}

            # Update or create ContestRanking
            ContestRanking.objects.update_or_create(
                contest=contest,
                user=r['user'],
                defaults={
                    'rank': r['rank'],
                    'solved': r['solved'],
                    'penalty': r['penalty'],
                    'score': float(r['solved'] * 100),
                    'problem_details': prob_map_by_prefix
                }
            )

            rows.append({
                'rank': r['rank'],
                'user_id': r['user'].id,
                'username': r['username'],
                'solved': r['solved'],
                'penalty': r['penalty'],
                'score': float(r['solved'] * 100),
                'problem_results': prob_map_by_prefix,
            })

        return {
            'contest': {
                'id': contest.id,
                'key': contest.key,
                'name': contest.name,
                'format': contest.format_name,
                'start_time': contest.start_time.isoformat() if contest.start_time else None,
                'end_time': contest.end_time.isoformat() if contest.end_time else None,
                'is_frozen': False,
            },
            'problems': problems_list,
            'rows': rows
        }

import os
import sys
import unittest
import urllib.request
import json
from datetime import datetime, timedelta

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
import django
django.setup()

from backend.ranking.calculators.score import ScoreCalculator
from backend.ranking.calculators.rank import RankCalculator
from backend.ranking.calculators.rating import CodeforcesRatingCalculator
from backend.ranking.calculators.percentile import PercentileCalculator
from backend.ranking.services.ranking_service import RankingService
from backend.ranking.services.contest_ranking_service import ContestRankingService
from backend.ranking.services.rating_service import RatingService
from backend.ranking.services.score_service import ScoreService

class RankingSystemIntegrationTest(unittest.TestCase):
    def test_01_score_calculator_icpc(self):
        start = datetime(2026, 1, 1, 10, 0, 0)
        subs = [
            {'problem_code': 'A', 'result': 'WA', 'date': start + timedelta(minutes=10)},
            {'problem_code': 'A', 'result': 'AC', 'date': start + timedelta(minutes=25)},
            {'problem_code': 'B', 'result': 'AC', 'date': start + timedelta(minutes=40)},
        ]
        res = ScoreCalculator.calculate_icpc(subs, start)
        self.assertEqual(res['solved'], 2)
        # Prob A: 25 + 20 = 45 penalty
        # Prob B: 40 penalty
        # Total = 85
        self.assertEqual(res['total_penalty'], 85)
        self.assertTrue(res['problems']['A']['is_solved'])
        self.assertTrue(res['problems']['B']['is_solved'])

    def test_02_rank_calculator_icpc(self):
        participants = [
            {'username': 'u1', 'solved': 2, 'penalty': 100},
            {'username': 'u2', 'solved': 3, 'penalty': 150},
            {'username': 'u3', 'solved': 2, 'penalty': 80},
        ]
        ranked = RankCalculator.rank_icpc(participants)
        self.assertEqual(ranked[0]['username'], 'u2')
        self.assertEqual(ranked[0]['rank'], 1)
        self.assertEqual(ranked[1]['username'], 'u3')
        self.assertEqual(ranked[1]['rank'], 2)
        self.assertEqual(ranked[2]['username'], 'u1')
        self.assertEqual(ranked[2]['rank'], 3)

    def test_03_codeforces_rating_calculator(self):
        contestants = [
            {'user_id': 1, 'rating': 1500, 'rank': 1},
            {'user_id': 2, 'rating': 1600, 'rank': 2},
            {'user_id': 3, 'rating': 1400, 'rank': 3},
        ]
        deltas = CodeforcesRatingCalculator.calculate_deltas(contestants)
        self.assertEqual(len(deltas), 3)
        # Winner (rank 1) should gain rating
        self.assertGreater(deltas[0]['delta'], 0)
        self.assertGreater(deltas[0]['new_rating'], 1500)

    def test_04_percentile_calculator(self):
        self.assertEqual(PercentileCalculator.calculate_percentile(1, 100), 100.0)
        self.assertEqual(PercentileCalculator.calculate_percentile(50, 100), 51.0)

    def test_05_api_endpoints_200(self):
        endpoints = [
            'http://127.0.0.1:8000/api/v1/rankings/global/',
            'http://127.0.0.1:8000/api/v1/rankings/contest/weekly-01/',
            'http://127.0.0.1:8000/api/v1/rankings/country/',
            'http://127.0.0.1:8000/api/v1/rankings/school/',
            'http://127.0.0.1:8000/api/v1/rankings/organization/',
            'http://127.0.0.1:8000/api/v1/rankings/users/tourist_vn/',
            'http://127.0.0.1:8000/api/v1/rankings/problems/APLUS/',
            'http://127.0.0.1:8000/api/v1/rankings/rating/',
            'http://127.0.0.1:8000/api/v1/rankings/history/tourist_vn/',
            'http://127.0.0.1:8000/api/v1/rankings/statistics/',
            'http://127.0.0.1:8000/api/v1/rankings/search/?q=tourist',
        ]
        for url in endpoints:
            req = urllib.request.urlopen(url)
            self.assertEqual(req.status, 200)
            data = json.loads(req.read().decode('utf-8'))
            self.assertIsNotNone(data)

    def test_06_frontend_pages_200(self):
        pages = [
            'http://localhost:8888/ranking',
            'http://localhost:8888/ranking/global',
            'http://localhost:8888/ranking/rating',
            'http://localhost:8888/ranking/contest',
            'http://localhost:8888/ranking/country',
            'http://localhost:8888/ranking/school',
            'http://localhost:8888/ranking/organization',
            'http://localhost:8888/ranking/history',
            'http://localhost:8888/ranking/user',
        ]
        for url in pages:
            req = urllib.request.urlopen(url)
            self.assertEqual(req.status, 200)

if __name__ == '__main__':
    unittest.main()

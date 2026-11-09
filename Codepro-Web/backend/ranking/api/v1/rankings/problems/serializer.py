from rest_framework import serializers

class ProblemSolverSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    submission_id = serializers.IntegerField()
    username = serializers.CharField()
    rating = serializers.IntegerField()
    tier = serializers.CharField()
    tier_color = serializers.CharField()
    time = serializers.FloatField()
    memory = serializers.FloatField()
    language = serializers.CharField()
    date = serializers.CharField()

class ProblemSolversResponseSerializer(serializers.Serializer):
    problem_code = serializers.CharField()
    problem_name = serializers.CharField()
    total_ac = serializers.IntegerField()
    solvers = ProblemSolverSerializer(many=True)
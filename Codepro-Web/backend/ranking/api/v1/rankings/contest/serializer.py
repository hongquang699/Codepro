from rest_framework import serializers

class ContestProblemSerializer(serializers.Serializer):
    prefix = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    points = serializers.FloatField()

class ContestRowSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    solved = serializers.IntegerField()
    penalty = serializers.IntegerField()
    score = serializers.FloatField()
    problem_results = serializers.DictField()

class ContestInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    key = serializers.CharField()
    name = serializers.CharField()
    format = serializers.CharField()
    start_time = serializers.CharField(allow_null=True)
    end_time = serializers.CharField(allow_null=True)
    is_frozen = serializers.BooleanField()

class ContestScoreboardSerializer(serializers.Serializer):
    contest = ContestInfoSerializer()
    problems = ContestProblemSerializer(many=True)
    rows = ContestRowSerializer(many=True)
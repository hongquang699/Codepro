#pragma once
#include <string>

struct JudgeTask {
    std::string submissionId;
    std::string problemCode;
    std::string language;
    int timeLimitMs;
    int memoryLimitMb;
};

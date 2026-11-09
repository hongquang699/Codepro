#!/bin/bash
javac Solution.java 2> compile.log
java -Xmx256m -Xss64m Solution

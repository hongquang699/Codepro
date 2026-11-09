const express = require('express');
const cors = require('cors');

const authRoutes = require('./auth/routes');
const userRoutes = require('./users/routes');
const problemRoutes = require('./problems/routes');
const submissionRoutes = require('./submissions/routes');
const contestRoutes = require('./contests/routes');
const courseRoutes = require('./courses/routes');
const lessonRoutes = require('./lessons/routes');
const discussionRoutes = require('./discussions/routes');
const commentRoutes = require('./comments/routes');
const blogRoutes = require('./blogs/routes');
const rankingRoutes = require('./rankings/routes');
const notificationRoutes = require('./notifications/routes');
const achievementRoutes = require('./achievements/routes');
const organizationRoutes = require('./organizations/routes');
const searchRoutes = require('./search/routes');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health Check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Register Domain Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/problems', problemRoutes);
app.use('/api/submissions', submissionRoutes);
app.use('/api/contests', contestRoutes);
app.use('/api/courses', courseRoutes);
app.use('/api/lessons', lessonRoutes);
app.use('/api/discussions', discussionRoutes);
app.use('/api/comments', commentRoutes);
app.use('/api/blogs', blogRoutes);
app.use('/api/rankings', rankingRoutes);
app.use('/api/notifications', notificationRoutes);
app.use('/api/achievements', achievementRoutes);
app.use('/api/organizations', organizationRoutes);
app.use('/api/search', searchRoutes);

// Error Handling Middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || 'Internal Server Error'
  });
});

module.exports = app;

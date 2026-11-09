const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all comments items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get comments detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created comments successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated comments successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted comments successfully');
};

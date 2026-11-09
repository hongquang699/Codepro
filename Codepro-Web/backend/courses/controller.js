const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all courses items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get courses detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created courses successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated courses successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted courses successfully');
};

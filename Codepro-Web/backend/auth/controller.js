const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all auth items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get auth detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created auth successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated auth successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted auth successfully');
};

const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all blogs items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get blogs detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created blogs successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated blogs successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted blogs successfully');
};

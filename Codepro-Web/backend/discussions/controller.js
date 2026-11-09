const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all discussions items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get discussions detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created discussions successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated discussions successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted discussions successfully');
};

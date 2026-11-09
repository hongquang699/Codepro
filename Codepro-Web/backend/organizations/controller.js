const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all organizations items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get organizations detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created organizations successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated organizations successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted organizations successfully');
};

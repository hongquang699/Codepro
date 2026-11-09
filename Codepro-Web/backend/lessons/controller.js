const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all lessons items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get lessons detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created lessons successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated lessons successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted lessons successfully');
};

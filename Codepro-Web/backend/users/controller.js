const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all users items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get users detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created users successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated users successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted users successfully');
};

const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all judge items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get judge detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created judge successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated judge successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted judge successfully');
};

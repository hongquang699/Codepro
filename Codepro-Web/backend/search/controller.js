const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all search items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get search detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created search successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated search successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted search successfully');
};

const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all problems items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get problems detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created problems successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated problems successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted problems successfully');
};

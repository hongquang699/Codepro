const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all submissions items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get submissions detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created submissions successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated submissions successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted submissions successfully');
};

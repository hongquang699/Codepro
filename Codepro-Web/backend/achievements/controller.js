const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all achievements items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get achievements detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created achievements successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated achievements successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted achievements successfully');
};

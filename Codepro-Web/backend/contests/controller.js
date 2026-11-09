const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all contests items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get contests detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created contests successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated contests successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted contests successfully');
};

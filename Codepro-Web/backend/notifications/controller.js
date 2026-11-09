const { success } = require('../core/response');

exports.getAll = async (req, res) => {
  return success(res, [], 'Get all notifications items');
};

exports.getById = async (req, res) => {
  return success(res, { id: req.params.id }, 'Get notifications detail');
};

exports.create = async (req, res) => {
  return success(res, { id: Date.now(), ...req.body }, 'Created notifications successfully', 201);
};

exports.update = async (req, res) => {
  return success(res, { id: req.params.id, ...req.body }, 'Updated notifications successfully');
};

exports.delete = async (req, res) => {
  return success(res, null, 'Deleted notifications successfully');
};

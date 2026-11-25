import api from './api';

export const connectionService = {
  async list() {
    const res = await api.get('/connections');
    return res.data;
  },

  async get(id) {
    const res = await api.get(`/connections/${id}`);
    return res.data;
  },

  async create(data) {
    const res = await api.post('/connections', data);
    return res.data;
  },

  async testNew(data) {
    const res = await api.post('/connections/test', data);
    return res.data;
  },

  async testExisting(id) {
    const res = await api.post(`/connections/${id}/test`);
    return res.data;
  },

  async delete(id) {
    const res = await api.delete(`/connections/${id}`);
    return res.data;
  },
};

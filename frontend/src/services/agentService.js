import api from './api';

export const agentService = {
  async list() {
    const res = await api.get('/agents');
    return res.data;
  },

  async register(name) {
    const res = await api.post('/agents/register', { name });
    return res.data;
  },

  async getStatus(id) {
    const res = await api.get(`/agents/${id}/status`);
    return res.data;
  },

  async revoke(id) {
    const res = await api.post(`/agents/${id}/revoke`);
    return res.data;
  },
};

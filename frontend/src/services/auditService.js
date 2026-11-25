import api from './api';

export const auditService = {
  async getLogs(params = {}) {
    const res = await api.get('/audit/logs', { params });
    return res.data;
  },
};

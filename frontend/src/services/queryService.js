import api from './api';

export const queryService = {
  async generateSql(data) {
    const res = await api.post('/query/generate', data);
    return res.data;
  },

  async executeSql(data) {
    const res = await api.post('/query/execute', data);
    return res.data;
  },

  async correctSql(data) {
    const res = await api.post('/query/correct', data);
    return res.data;
  },

  async explainSql(data) {
    const res = await api.post('/query/explain', data);
    return res.data;
  },

  async runPipeline(data) {
    const res = await api.post('/query/pipeline', data);
    return res.data;
  },

  async getHistory(params = {}) {
    const res = await api.get('/query/history', { params });
    return res.data;
  },
};

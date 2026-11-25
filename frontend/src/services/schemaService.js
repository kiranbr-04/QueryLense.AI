import api from './api';

export const schemaService = {
  async getSchema(connectionId) {
    const res = await api.get(`/connections/${connectionId}/schema`);
    return res.data;
  },

  async getExamples(connectionId) {
    const res = await api.get(`/connections/${connectionId}/examples`);
    return res.data;
  },

  async refreshSchema(connectionId) {
    const res = await api.post(`/connections/${connectionId}/schema/refresh`);
    return res.data;
  },

  async updateDescription(connectionId, tableId, description) {
    const res = await api.put(`/connections/${connectionId}/schema/${tableId}/description`, {
      business_description: description,
    });
    return res.data;
  },
};

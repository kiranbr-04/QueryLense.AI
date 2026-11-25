import React, { createContext, useContext, useState, useEffect } from 'react';
import { connectionService } from '../services/connectionService';
import { schemaService } from '../services/schemaService';
import { useAuth } from './AuthContext';

const DatabaseContext = createContext(null);

export const DatabaseProvider = ({ children }) => {
  const { user } = useAuth();
  const [connections, setConnections] = useState([]);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [schema, setSchema] = useState([]);
  const [loading, setLoading] = useState(false);
  const [schemaLoading, setSchemaLoading] = useState(false);

  const fetchConnections = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await connectionService.list();
      setConnections(data);
      if (data.length > 0 && !selectedConnection) {
        setSelectedConnection(data[0]);
      } else if (data.length === 0) {
        setSelectedConnection(null);
        setSchema([]);
      }
    } catch (e) {
      console.error('Failed to load connections:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchSchema = async (connectionId) => {
    if (!connectionId) return;
    setSchemaLoading(true);
    try {
      const data = await schemaService.getSchema(connectionId);
      setSchema(data);
    } catch (e) {
      console.error('Failed to load schema:', e);
      setSchema([]);
    } finally {
      setSchemaLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchConnections();
    } else {
      setConnections([]);
      setSelectedConnection(null);
      setSchema([]);
    }
  }, [user]);

  useEffect(() => {
    if (selectedConnection?.id) {
      fetchSchema(selectedConnection.id);
    }
  }, [selectedConnection]);

  return (
    <DatabaseContext.Provider
      value={{
        connections,
        selectedConnection,
        setSelectedConnection,
        schema,
        loading,
        schemaLoading,
        fetchConnections,
        fetchSchema: () => fetchSchema(selectedConnection?.id),
      }}
    >
      {children}
    </DatabaseContext.Provider>
  );
};

export const useDatabase = () => {
  const context = useContext(DatabaseContext);
  if (!context) {
    throw new Error('useDatabase must be used within a DatabaseProvider');
  }
  return context;
};

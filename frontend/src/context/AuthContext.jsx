import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('ql_token');
    const storedUser = localStorage.getItem('ql_user');
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
        // Verify with /me
        authService.getMe()
          .then((profile) => {
            const orgName = localStorage.getItem('ql_org_name') || 'Organization';
            const updated = { ...profile, organization_name: orgName };
            setUser(updated);
            localStorage.setItem('ql_user', JSON.stringify(updated));
          })
          .catch(() => {
            logout();
          })
          .finally(() => setLoading(false));
      } catch (e) {
        logout();
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await authService.login({ email, password });
    localStorage.setItem('ql_token', res.access_token);
    const userPayload = {
      id: res.user_id,
      email: res.email,
      role: res.role,
      organization_id: res.organization_id,
      organization_name: res.organization_name,
    };
    localStorage.setItem('ql_user', JSON.stringify(userPayload));
    localStorage.setItem('ql_org_name', res.organization_name);
    setUser(userPayload);
    return userPayload;
  };

  const register = async (email, password, fullName, organizationName) => {
    const res = await authService.register({
      email,
      password,
      full_name: fullName,
      organization_name: organizationName,
    });
    localStorage.setItem('ql_token', res.access_token);
    const userPayload = {
      id: res.user_id,
      email: res.email,
      role: res.role,
      organization_id: res.organization_id,
      organization_name: res.organization_name,
    };
    localStorage.setItem('ql_user', JSON.stringify(userPayload));
    localStorage.setItem('ql_org_name', res.organization_name);
    setUser(userPayload);
    return userPayload;
  };

  const logout = () => {
    localStorage.removeItem('ql_token');
    localStorage.removeItem('ql_user');
    localStorage.removeItem('ql_org_name');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

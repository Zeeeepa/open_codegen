import React, { createContext, useContext, useState, useEffect } from 'react';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import toast from 'react-hot-toast';

interface SupabaseContextType {
  supabase: SupabaseClient | null;
  isConnected: boolean;
  connect: (url: string, key: string) => Promise<boolean>;
  disconnect: () => void;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
}

const SupabaseContext = createContext<SupabaseContextType | undefined>(undefined);

export const useSupabase = () => {
  const context = useContext(SupabaseContext);
  if (context === undefined) {
    throw new Error('useSupabase must be used within a SupabaseProvider');
  }
  return context;
};

interface SupabaseProviderProps {
  children: React.ReactNode;
}

export const SupabaseProvider: React.FC<SupabaseProviderProps> = ({ children }) => {
  const [supabase, setSupabase] = useState<SupabaseClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');

  // Load saved connection from localStorage
  useEffect(() => {
    const savedUrl = localStorage.getItem('supabase_url');
    const savedKey = localStorage.getItem('supabase_key');
    
    if (savedUrl && savedKey) {
      connect(savedUrl, savedKey);
    }
  }, []);

  const connect = async (url: string, key: string): Promise<boolean> => {
    setConnectionStatus('connecting');
    
    try {
      // Create Supabase client
      const client = createClient(url, key);
      
      // Test connection by making a simple query
      const { error } = await client.from('endpoints').select('id').limit(1);
      
      if (error && !error.message.includes('relation "endpoints" does not exist')) {
        throw error;
      }
      
      // Connection successful
      setSupabase(client);
      setIsConnected(true);
      setConnectionStatus('connected');
      
      // Save connection details
      localStorage.setItem('supabase_url', url);
      localStorage.setItem('supabase_key', key);
      
      toast.success('Successfully connected to Supabase!');
      return true;
      
    } catch (error: any) {
      console.error('Supabase connection error:', error);
      setSupabase(null);
      setIsConnected(false);
      setConnectionStatus('error');
      
      toast.error(`Failed to connect to Supabase: ${error.message}`);
      return false;
    }
  };

  const disconnect = () => {
    setSupabase(null);
    setIsConnected(false);
    setConnectionStatus('disconnected');
    
    // Clear saved connection
    localStorage.removeItem('supabase_url');
    localStorage.removeItem('supabase_key');
    
    toast.success('Disconnected from Supabase');
  };

  const value: SupabaseContextType = {
    supabase,
    isConnected,
    connect,
    disconnect,
    connectionStatus,
  };

  return (
    <SupabaseContext.Provider value={value}>
      {children}
    </SupabaseContext.Provider>
  );
};

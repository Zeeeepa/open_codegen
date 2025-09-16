import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Database, Check, AlertCircle, Loader2 } from 'lucide-react';
import { useSupabase } from '../contexts/SupabaseContext';
import toast from 'react-hot-toast';

interface SupabaseConnectionForm {
  supabaseUrl: string;
  supabaseKey: string;
}

export const Settings: React.FC = () => {
  const { isConnected, connect, disconnect, connectionStatus } = useSupabase();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { register, handleSubmit, formState: { errors }, setValue } = useForm<SupabaseConnectionForm>({
    defaultValues: {
      supabaseUrl: localStorage.getItem('supabase_url') || '',
      supabaseKey: localStorage.getItem('supabase_key') || '',
    }
  });

  const onSubmit = async (data: SupabaseConnectionForm) => {
    setIsSubmitting(true);
    try {
      const success = await connect(data.supabaseUrl, data.supabaseKey);
      if (!success) {
        toast.error('Failed to connect to Supabase');
      }
    } catch (error) {
      toast.error('Connection failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDisconnect = () => {
    disconnect();
    setValue('supabaseUrl', '');
    setValue('supabaseKey', '');
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Check className="h-5 w-5 text-green-500" />;
      case 'connecting':
        return <Loader2 className="h-5 w-5 text-yellow-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Database className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected to Supabase';
      case 'connecting':
        return 'Connecting to Supabase...';
      case 'error':
        return 'Connection failed';
      default:
        return 'Not connected';
    }
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'connecting':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'error':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Configure your OpenCodegen instance and database connections.
        </p>
      </div>

      {/* Supabase Connection */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Database className="h-6 w-6 text-primary-600" />
            <h3 className="text-lg font-medium text-gray-900">Supabase Connection</h3>
          </div>

          {/* Connection Status */}
          <div className={`rounded-md border p-4 mb-6 ${getStatusColor()}`}>
            <div className="flex items-center space-x-3">
              {getStatusIcon()}
              <div>
                <p className="font-medium">{getStatusText()}</p>
                {connectionStatus === 'connected' && (
                  <p className="text-sm opacity-75">
                    Your endpoints and chat data will be stored in Supabase.
                  </p>
                )}
                {connectionStatus === 'error' && (
                  <p className="text-sm opacity-75">
                    Please check your URL and API key, then try again.
                  </p>
                )}
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label htmlFor="supabaseUrl" className="block text-sm font-medium text-gray-700">
                Supabase URL
              </label>
              <input
                type="url"
                id="supabaseUrl"
                {...register('supabaseUrl', {
                  required: 'Supabase URL is required',
                  pattern: {
                    value: /^https:\/\/[a-zA-Z0-9-]+\.supabase\.co$/,
                    message: 'Please enter a valid Supabase URL (e.g., https://your-project.supabase.co)'
                  }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                placeholder="https://your-project.supabase.co"
                disabled={isSubmitting}
              />
              {errors.supabaseUrl && (
                <p className="mt-1 text-sm text-red-600">{errors.supabaseUrl.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="supabaseKey" className="block text-sm font-medium text-gray-700">
                Supabase Anon Key
              </label>
              <input
                type="password"
                id="supabaseKey"
                {...register('supabaseKey', {
                  required: 'Supabase API key is required',
                  minLength: {
                    value: 100,
                    message: 'API key seems too short'
                  }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                disabled={isSubmitting}
              />
              {errors.supabaseKey && (
                <p className="mt-1 text-sm text-red-600">{errors.supabaseKey.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                You can find this in your Supabase project settings under API keys.
              </p>
            </div>

            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={isSubmitting || connectionStatus === 'connecting'}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Database className="h-4 w-4 mr-2" />
                    {isConnected ? 'Update Connection' : 'Connect to Supabase'}
                  </>
                )}
              </button>

              {isConnected && (
                <button
                  type="button"
                  onClick={handleDisconnect}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Disconnect
                </button>
              )}
            </div>
          </form>

          {/* Setup Instructions */}
          <div className="mt-8 p-4 bg-blue-50 rounded-md">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Setup Instructions</h4>
            <div className="text-sm text-blue-800 space-y-2">
              <p>1. Create a new project in <a href="https://supabase.com" target="_blank" rel="noopener noreferrer" className="underline">Supabase</a></p>
              <p>2. Go to Settings → API and copy your project URL and anon key</p>
              <p>3. Run the SQL schema setup in your Supabase SQL editor:</p>
              <div className="mt-2 p-2 bg-blue-100 rounded text-xs font-mono">
                <p>-- Create endpoints table</p>
                <p>CREATE TABLE endpoints (</p>
                <p>&nbsp;&nbsp;id TEXT PRIMARY KEY,</p>
                <p>&nbsp;&nbsp;name TEXT NOT NULL,</p>
                <p>&nbsp;&nbsp;url TEXT NOT NULL,</p>
                <p>&nbsp;&nbsp;method TEXT DEFAULT 'POST',</p>
                <p>&nbsp;&nbsp;headers JSONB DEFAULT '{}',</p>
                <p>&nbsp;&nbsp;model_name TEXT DEFAULT 'custom-model',</p>
                <p>&nbsp;&nbsp;text_input_selector TEXT DEFAULT '',</p>
                <p>&nbsp;&nbsp;send_button_selector TEXT DEFAULT '',</p>
                <p>&nbsp;&nbsp;response_selector TEXT DEFAULT '',</p>
                <p>&nbsp;&nbsp;variables JSONB DEFAULT '{}',</p>
                <p>&nbsp;&nbsp;user_id TEXT,</p>
                <p>&nbsp;&nbsp;is_active BOOLEAN DEFAULT true,</p>
                <p>&nbsp;&nbsp;created_at TIMESTAMP DEFAULT NOW(),</p>
                <p>&nbsp;&nbsp;updated_at TIMESTAMP DEFAULT NOW()</p>
                <p>);</p>
                <br />
                <p>-- Create conversations table</p>
                <p>CREATE TABLE conversations (</p>
                <p>&nbsp;&nbsp;id TEXT PRIMARY KEY,</p>
                <p>&nbsp;&nbsp;title TEXT NOT NULL,</p>
                <p>&nbsp;&nbsp;user_id TEXT NOT NULL,</p>
                <p>&nbsp;&nbsp;metadata JSONB DEFAULT '{}',</p>
                <p>&nbsp;&nbsp;created_at TIMESTAMP DEFAULT NOW(),</p>
                <p>&nbsp;&nbsp;updated_at TIMESTAMP DEFAULT NOW()</p>
                <p>);</p>
                <br />
                <p>-- Create messages table</p>
                <p>CREATE TABLE messages (</p>
                <p>&nbsp;&nbsp;id TEXT PRIMARY KEY,</p>
                <p>&nbsp;&nbsp;conversation_id TEXT REFERENCES conversations(id),</p>
                <p>&nbsp;&nbsp;role TEXT NOT NULL,</p>
                <p>&nbsp;&nbsp;content TEXT NOT NULL,</p>
                <p>&nbsp;&nbsp;endpoint_id TEXT REFERENCES endpoints(id),</p>
                <p>&nbsp;&nbsp;metadata JSONB DEFAULT '{}',</p>
                <p>&nbsp;&nbsp;created_at TIMESTAMP DEFAULT NOW()</p>
                <p>);</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Connect Supabase UI Component
 * 
 * Provides a user-friendly interface for connecting to Supabase with validation and testing.
 * Follows KISS principles with simple form handling and clear error messages.
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Database, CheckCircle, AlertCircle, Loader2, Eye, EyeOff } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

// Validation schema
const supabaseConfigSchema = z.object({
  url: z.string()
    .url('Please enter a valid Supabase URL')
    .refine(url => url.includes('supabase.co'), 'URL must be a valid Supabase URL'),
  anonKey: z.string()
    .min(1, 'Anonymous key is required')
    .min(100, 'Anonymous key appears to be too short'),
});

type SupabaseConfigForm = z.infer<typeof supabaseConfigSchema>;

interface ConnectSupabaseProps {
  onConnect: (config: SupabaseConfigForm) => Promise<boolean>;
  isConnected?: boolean;
  className?: string;
}

export const ConnectSupabase: React.FC<ConnectSupabaseProps> = ({
  onConnect,
  isConnected = false,
  className = '',
}) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
  } = useForm<SupabaseConfigForm>({
    resolver: zodResolver(supabaseConfigSchema),
    mode: 'onChange',
  });

  const handleConnect = async (data: SupabaseConfigForm) => {
    setIsConnecting(true);
    setConnectionStatus('idle');

    try {
      const success = await onConnect(data);
      
      if (success) {
        setConnectionStatus('success');
        toast.success('Successfully connected to Supabase!');
      } else {
        setConnectionStatus('error');
        toast.error('Failed to connect to Supabase. Please check your credentials.');
      }
    } catch (error) {
      setConnectionStatus('error');
      toast.error('Connection failed. Please try again.');
      console.error('Supabase connection error:', error);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = () => {
    reset();
    setConnectionStatus('idle');
    toast.success('Disconnected from Supabase');
  };

  if (isConnected) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`bg-green-50 border border-green-200 rounded-lg p-6 ${className}`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CheckCircle className="h-6 w-6 text-green-600" />
            <div>
              <h3 className="text-lg font-medium text-green-900">
                Connected to Supabase
              </h3>
              <p className="text-sm text-green-700">
                Your database connection is active and ready to use.
              </p>
            </div>
          </div>
          <button
            onClick={handleDisconnect}
            className="px-4 py-2 text-sm font-medium text-green-700 bg-green-100 
                     border border-green-300 rounded-md hover:bg-green-200 
                     focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
                     transition-colors duration-200"
          >
            Disconnect
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}
    >
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <Database className="h-6 w-6 text-blue-600" />
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Connect to Supabase
            </h3>
            <p className="text-sm text-gray-600">
              Enter your Supabase project credentials to get started.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit(handleConnect)} className="p-6 space-y-6">
        {/* Supabase URL Field */}
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
            Supabase URL
          </label>
          <input
            {...register('url')}
            type="url"
            id="url"
            placeholder="https://your-project.supabase.co"
            className={`w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                       ${errors.url ? 'border-red-300' : 'border-gray-300'}`}
          />
          {errors.url && (
            <p className="mt-1 text-sm text-red-600 flex items-center">
              <AlertCircle className="h-4 w-4 mr-1" />
              {errors.url.message}
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Find this in your Supabase project settings under "API"
          </p>
        </div>

        {/* Anonymous Key Field */}
        <div>
          <label htmlFor="anonKey" className="block text-sm font-medium text-gray-700 mb-2">
            Anonymous Key
          </label>
          <div className="relative">
            <input
              {...register('anonKey')}
              type={showKey ? 'text' : 'password'}
              id="anonKey"
              placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
              className={`w-full px-3 py-2 pr-10 border rounded-md shadow-sm placeholder-gray-400 
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                         ${errors.anonKey ? 'border-red-300' : 'border-gray-300'}`}
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              {showKey ? (
                <EyeOff className="h-4 w-4 text-gray-400 hover:text-gray-600" />
              ) : (
                <Eye className="h-4 w-4 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          {errors.anonKey && (
            <p className="mt-1 text-sm text-red-600 flex items-center">
              <AlertCircle className="h-4 w-4 mr-1" />
              {errors.anonKey.message}
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Your project's anonymous/public key (safe to use in frontend)
          </p>
        </div>

        {/* Connection Status */}
        {connectionStatus === 'error' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-red-50 border border-red-200 rounded-md p-4"
          >
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
              <p className="text-sm text-red-800">
                Connection failed. Please verify your credentials and try again.
              </p>
            </div>
          </motion.div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!isValid || isConnecting}
            className={`px-6 py-2 text-sm font-medium rounded-md focus:outline-none 
                       focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                       transition-all duration-200 flex items-center space-x-2
                       ${!isValid || isConnecting
                         ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                         : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow-md'
                       }`}
          >
            {isConnecting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Connecting...</span>
              </>
            ) : (
              <>
                <Database className="h-4 w-4" />
                <span>Connect to Supabase</span>
              </>
            )}
          </button>
        </div>

        {/* Help Text */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">
            Need help finding your credentials?
          </h4>
          <ol className="text-xs text-blue-800 space-y-1 list-decimal list-inside">
            <li>Go to your Supabase project dashboard</li>
            <li>Navigate to Settings → API</li>
            <li>Copy the "Project URL" and "anon public" key</li>
            <li>Paste them into the fields above</li>
          </ol>
        </div>
      </form>
    </motion.div>
  );
};

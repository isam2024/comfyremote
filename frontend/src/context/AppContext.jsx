/**
 * Global application state using React Context
 */
import { createContext, useContext, useReducer, useCallback, useMemo } from 'react';

const AppContext = createContext();

// Initial state
const initialState = {
  pods: {},
  gpus: [],
  costSummary: {
    total_cost: 0,
    total_pods: 0,
    by_gpu: {},
  },
  selectedPodId: null,
  loading: false,
  error: null,
};

// Action types
const ActionTypes = {
  SET_PODS: 'SET_PODS',
  ADD_POD: 'ADD_POD',
  UPDATE_POD: 'UPDATE_POD',
  REMOVE_POD: 'REMOVE_POD',
  SET_GPUS: 'SET_GPUS',
  SET_COST_SUMMARY: 'SET_COST_SUMMARY',
  SELECT_POD: 'SELECT_POD',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
};

// Reducer
function appReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_PODS: {
      const pods = {};
      action.payload.forEach(pod => {
        pods[pod.pod_id] = pod;
      });
      return { ...state, pods, loading: false };
    }

    case ActionTypes.ADD_POD: {
      const newPod = action.payload;
      return {
        ...state,
        pods: {
          ...state.pods,
          [newPod.pod_id]: newPod,
        },
      };
    }

    case ActionTypes.UPDATE_POD: {
      const { podId, updates } = action.payload;
      const existing = state.pods[podId];

      if (!existing) return state;

      return {
        ...state,
        pods: {
          ...state.pods,
          [podId]: {
            ...existing,
            ...updates,
          },
        },
      };
    }

    case ActionTypes.REMOVE_POD: {
      const { [action.payload]: removed, ...remainingPods } = state.pods;
      return { ...state, pods: remainingPods };
    }

    case ActionTypes.SET_GPUS:
      return { ...state, gpus: action.payload };

    case ActionTypes.SET_COST_SUMMARY:
      return { ...state, costSummary: action.payload };

    case ActionTypes.SELECT_POD:
      return { ...state, selectedPodId: action.payload };

    case ActionTypes.SET_LOADING:
      return { ...state, loading: action.payload };

    case ActionTypes.SET_ERROR:
      return { ...state, error: action.payload };

    default:
      return state;
  }
}

// Provider component
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Actions - memoized to prevent infinite loops
  const actions = useMemo(() => ({
    setPods: (pods) => {
      dispatch({ type: ActionTypes.SET_PODS, payload: pods });
    },

    addPod: (pod) => {
      dispatch({ type: ActionTypes.ADD_POD, payload: pod });
    },

    updatePod: (podId, updates) => {
      dispatch({ type: ActionTypes.UPDATE_POD, payload: { podId, updates } });
    },

    removePod: (podId) => {
      dispatch({ type: ActionTypes.REMOVE_POD, payload: podId });
    },

    setGpus: (gpus) => {
      dispatch({ type: ActionTypes.SET_GPUS, payload: gpus });
    },

    setCostSummary: (summary) => {
      dispatch({ type: ActionTypes.SET_COST_SUMMARY, payload: summary });
    },

    selectPod: (podId) => {
      dispatch({ type: ActionTypes.SELECT_POD, payload: podId });
    },

    setLoading: (loading) => {
      dispatch({ type: ActionTypes.SET_LOADING, payload: loading });
    },

    setError: (error) => {
      dispatch({ type: ActionTypes.SET_ERROR, payload: error });
    },
  }), []);

  const value = useMemo(() => ({ state, actions }), [state, actions]);

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook to use context
export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}

export default AppContext;

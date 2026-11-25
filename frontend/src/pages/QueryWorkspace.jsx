import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  Play, 
  RotateCcw, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  BarChart3, 
  Table, 
  Clock, 
  Hash, 
  Send,
  MessageSquare,
  Wand2,
  ChevronRight,
  Database,
  Lightbulb,
  Check
} from 'lucide-react';
import { useDatabase } from '../context/DatabaseContext';
import { queryService } from '../services/queryService';
import { schemaService } from '../services/schemaService';
import { SqlEditor } from '../components/SqlEditor';
import { ResultsTable } from '../components/ResultsTable';
import { DataVisualizer } from '../components/DataVisualizer';
import { StatusBadge } from '../components/StatusBadge';

export const QueryWorkspace = ({ initialPrompt, initialSql }) => {
  const { selectedConnection, schema } = useDatabase();

  const [question, setQuestion] = useState(initialPrompt || '');
  const [conversationId, setConversationId] = useState(() => 'conv_' + Date.now());
  const [conversationTurns, setConversationTurns] = useState([]);
  
  const [generatedSql, setGeneratedSql] = useState(initialSql || '');
  const [isValidSql, setIsValidSql] = useState(true);
  const [validationError, setValidationError] = useState(null);

  const [generating, setGenerating] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [activeView, setActiveView] = useState('both'); // 'table' | 'chart' | 'both'

  // Dynamic schema suggestions
  const [examples, setExamples] = useState([]);
  const [loadingExamples, setLoadingExamples] = useState(false);

  // Query Result State
  const [queryResult, setQueryResult] = useState(null);
  const [executionError, setExecutionError] = useState(null);
  const [correctionNotice, setCorrectionNotice] = useState(null);
  const [threadNotice, setThreadNotice] = useState(null);

  const inputRef = useRef(null);

  useEffect(() => {
    if (initialPrompt && initialPrompt !== question) {
      setQuestion(initialPrompt);
    }
    if (initialSql && initialSql !== generatedSql) {
      setGeneratedSql(initialSql);
    }
  }, [initialPrompt, initialSql]);

  // Load dynamic schema-driven suggestions whenever selectedConnection changes
  useEffect(() => {
    let isMounted = true;
    if (selectedConnection?.id) {
      setLoadingExamples(true);
      schemaService.getExamples(selectedConnection.id)
        .then((data) => {
          if (isMounted) {
            setExamples(Array.isArray(data) && data.length > 0 ? data : []);
          }
        })
        .catch(() => {
          if (isMounted) setExamples([]);
        })
        .finally(() => {
          if (isMounted) setLoadingExamples(false);
        });
    } else {
      setExamples([]);
    }
    return () => {
      isMounted = false;
    };
  }, [selectedConnection?.id]);

  // 1. Natural Language Query Pipeline (Synthesis + Auto-Correction + Execution + Explanation)
  const runNaturalLanguageQuery = async (queryText) => {
    const textToRun = queryText || question;
    if (!textToRun || !selectedConnection) return;

    setGenerating(true);
    setExecutionError(null);
    setCorrectionNotice(null);

    try {
      const res = await queryService.runPipeline({
        connection_id: selectedConnection.id,
        question: textToRun,
        conversation_id: conversationId,
        auto_correct: true,
      });

      setQueryResult(res);
      setGeneratedSql(res.executed_sql || '');
      setIsValidSql(res.success || !res.error);

      if (res.success) {
        setConversationTurns((prev) => [
          ...prev,
          {
            question: textToRun,
            executedSql: res.executed_sql,
            rowCount: res.row_count,
            timeMs: res.execution_time_ms,
            explanation: res.ai_explanation,
          },
        ]);
      } else {
        setExecutionError(res.error || 'Execution failed.');
      }
    } catch (err) {
      setExecutionError(err.response?.data?.detail || err.message || 'Execution error.');
    } finally {
      setGenerating(false);
    }
  };

  const handleFormSubmit = (e) => {
    if (e) e.preventDefault();
    runNaturalLanguageQuery(question);
  };

  // Clicking a suggestion sets input and immediately runs query
  const handleSuggestionClick = (suggestionText) => {
    setQuestion(suggestionText);
    runNaturalLanguageQuery(suggestionText);
  };

  // 2. Exact SQL Execution from Monaco Editor (runs edited SQL as edited)
  const handleExecuteExactSql = async (sqlToRun) => {
    const queryToExecute = typeof sqlToRun === 'string' ? sqlToRun : generatedSql;
    if (!selectedConnection || !queryToExecute) return;

    setExecuting(true);
    setExecutionError(null);

    try {
      const res = await queryService.executeSql({
        connection_id: selectedConnection.id,
        sql: queryToExecute,
        question: question || 'Direct SQL Execution',
        conversation_id: conversationId,
        auto_explain: true,
      });

      setQueryResult(res);
      setGeneratedSql(res.executed_sql || queryToExecute);
      setIsValidSql(res.success);

      if (res.success) {
        setConversationTurns((prev) => [
          ...prev,
          {
            question: question || 'Manual SQL Edit',
            executedSql: res.executed_sql,
            rowCount: res.row_count,
            timeMs: res.execution_time_ms,
            explanation: res.ai_explanation,
          },
        ]);
      } else {
        setExecutionError(res.error || 'Execution failed.');
      }
    } catch (err) {
      setExecutionError(err.response?.data?.detail || err.message || 'Execution error.');
    } finally {
      setExecuting(false);
    }
  };

  // 3. Reset Thread
  const handleNewThread = () => {
    const newId = 'conv_' + Date.now();
    setConversationId(newId);
    setConversationTurns([]);
    setQueryResult(null);
    setQuestion('');
    setGeneratedSql('');
    setExecutionError(null);
    setCorrectionNotice(null);
    setThreadNotice('New conversation thread initialized.');
    setTimeout(() => setThreadNotice(null), 3000);
    if (inputRef.current) inputRef.current.focus();
  };

  // Check if query results have numeric columns suitable for visualization
  const hasNumericMetrics = queryResult?.success && 
    Array.isArray(queryResult?.columns) && 
    queryResult.columns.some((c) => c.type === 'number') &&
    Array.isArray(queryResult?.rows) && 
    queryResult.rows.length > 0;

  return (
    <div className="space-y-6">
      {/* Top Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-600" />
            AI Query Workspace
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Targeting database:{' '}
            <span className="font-semibold text-slate-800">{selectedConnection?.name || 'None selected'}</span>{' '}
            <span className="font-mono text-[11px] bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 uppercase font-semibold text-slate-700 ml-1">
              {selectedConnection?.dialect || 'unknown'}
            </span>
            <span className="ml-2 inline-flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              {selectedConnection?.status === 'connected' ? 'Connected' : 'Active'}
            </span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {threadNotice && (
            <span className="text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200 animate-fade-in flex items-center gap-1">
              <Check className="w-3 h-3 text-emerald-600" /> {threadNotice}
            </span>
          )}
          <button
            onClick={handleNewThread}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 bg-white hover:bg-slate-50 shadow-xs transition"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-400" /> New Thread
          </button>
        </div>
      </div>

      {/* Query Control Section */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
        
        {/* Dynamic Schema-Driven Suggestions (STRICTLY ABOVE Natural Language Input Bar) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
              Dynamic Schema Suggestions
              <span className="text-[11px] font-normal text-slate-400">
                (Tailored to {selectedConnection?.database_name || 'connected database'} schema)
              </span>
            </span>
            {loadingExamples && (
              <span className="text-[11px] text-slate-400 animate-pulse">Inspecting schema...</span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {examples.length > 0 ? (
              examples.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  disabled={generating || executing}
                  onClick={() => handleSuggestionClick(s)}
                  className="group inline-flex items-center gap-1.5 text-xs text-slate-700 hover:text-brand-700 bg-slate-50 hover:bg-brand-50 hover:border-brand-300 px-3 py-1.5 rounded-lg border border-slate-200 transition text-left shadow-2xs disabled:opacity-50"
                >
                  <Sparkles className="w-3 h-3 text-brand-500 shrink-0 group-hover:scale-110 transition-transform" />
                  <span>{s}</span>
                </button>
              ))
            ) : !loadingExamples ? (
              <div className="text-xs text-slate-400 italic">
                Connect a database with tables to inspect dynamic query suggestions.
              </div>
            ) : null}
          </div>
        </div>

        {/* Natural Language Question Input (STRICTLY BELOW Suggestions) */}
        <form onSubmit={handleFormSubmit} className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <MessageSquare className="w-3.5 h-3.5 text-brand-600" />
              Ask Question in Natural Language
            </label>
            {conversationTurns.length > 0 && (
              <span className="text-[11px] font-mono text-brand-700 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200 font-semibold">
                Turn #{conversationTurns.length + 1} in context
              </span>
            )}
          </div>

          <div className="relative flex items-center">
            <input
              ref={inputRef}
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  runNaturalLanguageQuery(question);
                }
              }}
              placeholder="Ask anything about your database in natural language (e.g. 'Show employees whose salary is 50000')..."
              className="w-full bg-slate-50 border border-slate-300 rounded-xl pl-4 pr-36 py-3.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white transition"
            />
            <button
              type="submit"
              disabled={generating || executing || !question.trim() || !selectedConnection}
              className="absolute right-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-lg text-xs flex items-center gap-1.5 shadow-xs transition disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Wand2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Synthesizing...</span>
                </>
              ) : executing ? (
                <>
                  <Play className="w-3.5 h-3.5 animate-pulse" />
                  <span>Running...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Ask QueryLens</span>
                </>
              )}
            </button>
          </div>
        </form>

      </div>

      {/* Monaco SQL Editor & Security Guardrail (Executes Exact SQL on User Run) */}
      {(generatedSql || generating) && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-700">Dialect-Aware SQL Query</span>
              {isValidSql ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <ShieldCheck className="w-3 h-3" /> Read-Only Validated
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                  <AlertCircle className="w-3 h-3" /> Security Warning: {validationError}
                </span>
              )}
            </div>

            <span className="text-[11px] text-slate-400 font-mono">
              Dialect: <span className="text-slate-700 font-bold uppercase">{selectedConnection?.dialect || 'SQL'}</span>
            </span>
          </div>

          <SqlEditor
            value={generatedSql}
            onChange={(val) => setGeneratedSql(val)}
            onExecute={() => handleExecuteExactSql(generatedSql)}
            readOnly={false}
            height="150px"
          />
        </div>
      )}

      {/* Execution Errors */}
      {executionError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-rose-800">Database Execution Failed</h4>
            <p className="text-xs text-rose-700 mt-1 font-mono">{executionError}</p>
          </div>
        </div>
      )}

      {/* AI Grounded Result Explanation */}
      {queryResult?.success && queryResult?.ai_explanation && (
        <div className="bg-gradient-to-r from-brand-50/70 via-indigo-50/40 to-white border border-brand-200/80 rounded-xl p-4 shadow-xs">
          <div className="flex items-center gap-2 text-brand-800 text-xs font-bold mb-1.5">
            <Sparkles className="w-4 h-4 text-brand-600" />
            <span>AI Business Intelligence Explanation</span>
            <span className="text-[10px] font-normal text-slate-400 ml-1">
              (Grounded strictly in retrieved database records)
            </span>
          </div>
          <p className="text-xs text-slate-800 leading-relaxed font-medium">
            {queryResult.ai_explanation}
          </p>
        </div>
      )}

      {/* Exact Records & Visualizations Panel */}
      {queryResult?.success && (
        <div className="space-y-4">
          {/* Tabs for Table vs Visualization */}
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveView('both')}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                  activeView === 'both' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Split View
              </button>
              <button
                onClick={() => setActiveView('table')}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                  activeView === 'table' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Data Table ({queryResult.row_count})
              </button>
              {hasNumericMetrics && (
                <button
                  onClick={() => setActiveView('chart')}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                    activeView === 'chart' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Chart Visualization
                </button>
              )}
            </div>

            <div className="flex items-center gap-3 text-xs font-mono text-slate-500">
              <span className="flex items-center gap-1">
                <Hash className="w-3.5 h-3.5 text-slate-400" /> {queryResult.row_count} rows
              </span>
              <span className="flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                <Clock className="w-3.5 h-3.5" /> {queryResult.execution_time_ms} ms
              </span>
            </div>
          </div>

          {/* Visualizer (rendered only when active and numeric metrics exist) */}
          {hasNumericMetrics && (activeView === 'chart' || activeView === 'both') && (
            <DataVisualizer
              columns={queryResult.columns}
              rows={queryResult.rows}
              suggestion={queryResult.chart_suggestion}
            />
          )}

          {/* Data Table */}
          {(activeView === 'table' || activeView === 'both' || !hasNumericMetrics) && (
            <ResultsTable
              columns={queryResult.columns}
              rows={queryResult.rows}
              executionTimeMs={queryResult.execution_time_ms}
              rowCount={queryResult.row_count}
              truncated={queryResult.truncated}
            />
          )}
        </div>
      )}
    </div>
  );
};

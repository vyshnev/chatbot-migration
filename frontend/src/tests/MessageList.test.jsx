import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MessageList } from '../components/chat/MessageList';
import { parseSources, groupMessages } from '../components/chat/MessageList';

// ---------------------------------------------------------------------------
// parseSources — pure function tests
// ---------------------------------------------------------------------------
describe('parseSources', () => {
  it('returns the full content as body when no Sources section exists', () => {
    const { body, sources } = parseSources('Hello world');
    expect(body).toBe('Hello world');
    expect(sources).toHaveLength(0);
  });

  it('splits on **Sources:** and extracts markdown links', () => {
    const content = 'Some answer.\n\n**Sources:**\n- [CNN](https://cnn.com)\n- [BBC](https://bbc.com)';
    const { body, sources } = parseSources(content);

    expect(body).toBe('Some answer.');
    expect(sources).toHaveLength(2);
    expect(sources[0]).toEqual({ label: 'CNN', url: 'https://cnn.com' });
    expect(sources[1]).toEqual({ label: 'BBC', url: 'https://bbc.com' });
  });

  it('splits on plain Sources: without bold markers', () => {
    const content = 'Answer.\n\nSources:\n[Wikipedia](https://en.wikipedia.org/wiki/Test)';
    const { body, sources } = parseSources(content);

    expect(body).toBe('Answer.');
    expect(sources[0].url).toBe('https://en.wikipedia.org/wiki/Test');
  });

  it('returns empty sources array when Sources: section has no complete links yet (streaming mid-way)', () => {
    const content = 'Answer.\n\n**Sources:**\n- [CNN](https://c'; // incomplete URL
    const { body, sources } = parseSources(content);

    // Body is still clean (Sources: stripped)
    expect(body).toBe('Answer.');
    // No complete links parsed yet
    expect(sources).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// groupMessages — pure function tests
// ---------------------------------------------------------------------------
describe('groupMessages', () => {
  it('returns empty array for empty input', () => {
    expect(groupMessages([])).toHaveLength(0);
  });

  it('groups consecutive tool messages into one tool_group', () => {
    const messages = [
      { id: '1', role: 'user', content: 'Hi' },
      { id: '2', role: 'tool', name: 'search_tool', content: 'results' },
      { id: '3', role: 'tool', name: 'read_webpage', content: 'page' },
      { id: '4', role: 'assistant', content: 'Answer' },
    ];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(3);
    expect(groups[0].type).toBe('user');
    expect(groups[1].type).toBe('tool_group');
    expect(groups[1].messages).toHaveLength(2);
    expect(groups[2].type).toBe('assistant');
  });

  it('creates separate groups for non-consecutive tool messages', () => {
    const messages = [
      { id: '1', role: 'tool', name: 'search_tool', content: 'r1' },
      { id: '2', role: 'assistant', content: 'A' },
      { id: '3', role: 'tool', name: 'read_webpage', content: 'r2' },
    ];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(3);
    expect(groups[0].type).toBe('tool_group');
    expect(groups[1].type).toBe('assistant');
    expect(groups[2].type).toBe('tool_group');
  });

  it('handles a single tool message as a group of 1', () => {
    const messages = [{ id: '1', role: 'tool', name: 'calculator', content: '42' }];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(1);
    expect(groups[0].type).toBe('tool_group');
    expect(groups[0].messages).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// MessageList component — rendering tests
// ---------------------------------------------------------------------------
describe('MessageList Component', () => {
  it('renders a user message correctly', () => {
    const messages = [
      { id: 'u1', role: 'user', content: 'Hello this is a test user message' }
    ];

    render(<MessageList messages={messages} messagesEndRef={{ current: null }} />);

    expect(screen.getByText('Hello this is a test user message')).toBeInTheDocument();
  });

  it('renders tool messages in a grouped collapsible (ToolGroup)', () => {
    // Use realistic read_webpage output: getShortContext() extracts hostname as context label
    // so the raw body text is only visible after the second (raw output) expand
    const messages = [
      {
        id: 'tool-1',
        role: 'tool',
        name: 'read_webpage',
        content: 'Source: https://en.wikipedia.org/wiki/Test\n\nThis is the hidden raw page body.',
      }
    ];

    render(<MessageList messages={messages} messagesEndRef={{ current: null }} />);

    // Collapsed header shows step count (singular)
    expect(screen.getByText('1 step')).toBeInTheDocument();

    // Raw body is hidden initially
    expect(screen.queryByText(/This is the hidden raw page body/)).not.toBeInTheDocument();

    // Click the group header to expand the tool list
    const groupHeader = screen.getByText('1 step').closest('button');
    fireEvent.click(groupHeader);

    // Individual "Webpage Reader" row and hostname context are now visible
    expect(screen.getByText('Webpage Reader')).toBeInTheDocument();
    expect(screen.getByText('en.wikipedia.org')).toBeInTheDocument();

    // But raw body is still hidden (needs second click on the individual row)
    expect(screen.queryByText(/This is the hidden raw page body/)).not.toBeInTheDocument();

    // Click the individual tool row to reveal raw output
    const toolRow = screen.getByText('Webpage Reader').closest('button');
    fireEvent.click(toolRow);

    // Raw body is now visible (div contains the full content including "Source:" prefix)
    expect(screen.getByText(/This is the hidden raw page body/)).toBeInTheDocument();
  });

  it('renders 2 tool messages as a single group with "2 steps" in header', () => {
    const messages = [
      { id: 't1', role: 'tool', name: 'search_tool', content: 'results' },
      { id: 't2', role: 'tool', name: 'read_webpage', content: 'page content' },
    ];

    render(<MessageList messages={messages} messagesEndRef={{ current: null }} />);

    expect(screen.getByText('2 steps')).toBeInTheDocument();
    // Only one group header exists (not two separate accordions)
    expect(screen.getAllByText(/steps/)).toHaveLength(1);
  });
});

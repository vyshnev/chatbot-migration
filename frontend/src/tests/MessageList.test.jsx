import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MessageList } from '../components/chat/MessageList';

describe('MessageList Component', () => {
  it('renders a user message correctly', () => {
    const messages = [
      { role: 'user', content: 'Hello this is a test user message' }
    ];
    
    render(<MessageList messages={messages} />);
    
    // Check if the message content is displayed
    expect(screen.getByText('Hello this is a test user message')).toBeInTheDocument();
  });

  it('renders tool messages as a collapsible accordion', () => {
    const messages = [
      { role: 'tool', name: 'read_webpage', content: 'Huge scraped text here' }
    ];
    
    render(<MessageList messages={messages} />);
    
    // It should render the mapped friendly name, not the raw name
    expect(screen.getByText('Webpage Reader')).toBeInTheDocument();
    
    // The raw content should be hidden initially (isOpen is false)
    expect(screen.queryByText('Huge scraped text here')).not.toBeInTheDocument();
    
    // Click the accordion pill
    const pill = screen.getByText('Webpage Reader').closest('div');
    fireEvent.click(pill);
    
    // The raw content should now be visible
    expect(screen.getByText('Huge scraped text here')).toBeInTheDocument();
  });
});

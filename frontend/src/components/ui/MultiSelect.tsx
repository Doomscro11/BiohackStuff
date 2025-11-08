// MultiSelect component for chemistry options
import React, { useState } from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { X } from 'lucide-react';

export interface MultiSelectOption {
  label: string;
  value: string;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (values: string[]) => void;
  max?: number;
  placeholder?: string;
  className?: string;
}

export default function MultiSelect({
  options,
  value,
  onChange,
  max,
  placeholder = 'Select options...',
  className = ''
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  
  const handleToggle = (optionValue: string) => {
    if (value.includes(optionValue)) {
      // Remove
      onChange(value.filter(v => v !== optionValue));
    } else {
      // Add (if under max limit)
      if (!max || value.length < max) {
        onChange([...value, optionValue]);
      }
    }
  };
  
  const handleRemove = (optionValue: string) => {
    onChange(value.filter(v => v !== optionValue));
  };
  
  const selectedLabels = options
    .filter(opt => value.includes(opt.value))
    .map(opt => opt.label);
  
  return (
    <div className={`relative ${className}`}>
      {/* Selected badges */}
      <div className="flex flex-wrap gap-2 mb-2">
        {selectedLabels.map((label, idx) => (
          <Badge
            key={idx}
            variant="secondary"
            className="flex items-center gap-1 text-xs"
          >
            {label}
            <X
              className="h-3 w-3 cursor-pointer hover:text-red-500"
              onClick={() => handleRemove(value[idx])}
            />
          </Badge>
        ))}
        {selectedLabels.length === 0 && (
          <span className="text-sm text-gray-400">{placeholder}</span>
        )}
      </div>
      
      {/* Options list */}
      <div className="border rounded-md p-2 max-h-48 overflow-y-auto space-y-2">
        {options.map((option) => {
          const isSelected = value.includes(option.value);
          const isDisabled = !isSelected && max && value.length >= max;
          
          return (
            <label
              key={option.value}
              className={`flex items-center space-x-2 cursor-pointer p-1 rounded hover:bg-gray-50 ${
                isDisabled ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <Checkbox
                checked={isSelected}
                onCheckedChange={() => !isDisabled && handleToggle(option.value)}
                disabled={isDisabled}
              />
              <span className="text-sm flex-1">{option.label}</span>
            </label>
          );
        })}
      </div>
      
      {max && (
        <div className="text-xs text-gray-500 mt-1">
          {value.length} / {max} selected
        </div>
      )}
    </div>
  );
}

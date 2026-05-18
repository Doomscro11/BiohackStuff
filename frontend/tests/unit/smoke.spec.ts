import { cn } from '@/lib/utils';
import { canAccessAdmin } from '@/lib/roles';

describe('frontend smoke tests', () => {
  it('merges class names through cn utility', () => {
    expect(cn('px-2', false && 'hidden', 'py-1')).toContain('px-2');
    expect(cn('px-2', false && 'hidden', 'py-1')).toContain('py-1');
  });

  it('recognizes admin access for admin role', () => {
    expect(canAccessAdmin({ role: 'admin' })).toBe(true);
  });

  it('does not grant admin access to anonymous users', () => {
    expect(canAccessAdmin(null)).toBe(false);
  });
});

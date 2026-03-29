import { NextRequest, NextResponse } from 'next/server';

// Paths that don't require authentication
const PUBLIC_PATHS = ['/login', '/change-password'];
// Paths that logged-in users should NOT be redirected away from
// (e.g. /change-password must remain accessible after login when force_password_change=true)
const ALWAYS_ACCESSIBLE_WHEN_LOGGED_IN = ['/change-password'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic   = PUBLIC_PATHS.some(p => pathname.startsWith(p));
  const isLoggedIn = request.cookies.has('glih_logged_in');
  const alwaysAllow = ALWAYS_ACCESSIBLE_WHEN_LOGGED_IN.some(p => pathname.startsWith(p));

  // Redirect logged-in users away from /login only (not /change-password)
  if (isPublic && isLoggedIn && !alwaysAllow) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  if (!isPublic && !isLoggedIn) {
    const url = new URL('/login', request.url);
    url.searchParams.set('from', pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.png$).*)'],
};

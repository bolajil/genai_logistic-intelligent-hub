import { NextRequest, NextResponse } from 'next/server';

const PUBLIC_PATHS = ['/login', '/change-password'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic   = PUBLIC_PATHS.some(p => pathname.startsWith(p));
  const isLoggedIn = request.cookies.has('glih_logged_in');

  if (isPublic && isLoggedIn) {
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

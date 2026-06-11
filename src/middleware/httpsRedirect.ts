import { Request, Response, NextFunction } from 'express';

export function httpsRedirect(req: Request, res: Response, next: NextFunction) {
  // In production, enforce HTTPS. Skip when running locally.
  if (process.env.NODE_ENV !== 'development') {
    const proto = req.headers['x-forwarded-proto'] as string | undefined;
    if (proto && proto !== 'https') {
      const host = req.get('host');
      return res.redirect(`https://${host}${req.originalUrl}`);
    }
    if (!req.secure && !(proto && proto === 'https')) {
      const host = req.get('host');
      return res.redirect(`https://${host}${req.originalUrl}`);
    }
  }
  next();
}

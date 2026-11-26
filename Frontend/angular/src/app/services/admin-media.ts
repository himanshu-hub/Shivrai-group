
import { Injectable, inject } from '@angular/core';

import {
  HttpClient,
  HttpHeaders,
  HttpParams
} from '@angular/common/http';

import { Observable } from 'rxjs';
import { AuthService } from './auth';


export type ImageUsage =
  | 'all'
  | 'used'
  | 'unused'
  | 'cover'
  | 'gallery';

export type ImageSort =
  | 'newest'
  | 'oldest'
  | 'filename_asc'
  | 'filename_desc';


export interface MediaUsageReference {
  project_id: string;
  project_name: string;
  role: 'cover' | 'gallery';
}


export interface MediaImage {
  id: string;
  public_id: string;
  image_url: string;
  filename: string | null;
  uploaded_at: string | null;
  in_use: boolean;
  used_in: MediaUsageReference[];
}


export interface MediaDetails extends MediaImage {
  usage_count: number;
  can_delete: boolean;
}


export interface MediaListResponse {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
  images: MediaImage[];
}


export interface MediaStatsResponse {
  total_images: number;
  used_images: number;
  unused_images: number;
  cover_images: number;
  gallery_images: number;
  total_projects: number;

  projects: {
    project_id: string;
    project_name: string;
    cover_count: number;
    gallery_count: number;
    total_images: number;
  }[];
}


export interface UploadImageResponse {
  message: string;
  media_id: string;
  image_url: string;
  public_id: string;
  saved_in_media_library: boolean;
}


export interface GalleryOrderResponse {
  message: string;
  project_id: string;
  gallery: string[];
  gallery_assets: {
    url: string;
    public_id: string;
  }[];
  total_images: number;
}


@Injectable({
  providedIn: 'root'
})
export class AdminMediaService {

  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  private readonly baseUrl =
    'http://127.0.0.1:8000/images';


  private options() {
    const token = this.auth.getToken();

    if (!token) {
      throw new Error(
        'Admin session expired. Please log in again.'
      );
    }

    return {
      headers: new HttpHeaders({
        Authorization: `Bearer ${token}`
      })
    };
  }


  // ==========================================
  // GET MEDIA LIBRARY
  // ==========================================

  getImages(params: {
    page: number;
    limit: number;
    search: string;
    usage: ImageUsage;
    sort_by: ImageSort;
  }): Observable<MediaListResponse> {

    let query = new HttpParams()
      .set('page', params.page)
      .set('limit', params.limit)
      .set('usage', params.usage)
      .set('sort_by', params.sort_by);

    if (params.search.trim()) {
      query = query.set(
        'search',
        params.search.trim()
      );
    }

    return this.http.get<MediaListResponse>(
      `${this.baseUrl}/`,
      {
        ...this.options(),
        params: query
      }
    );
  }


  // ==========================================
  // MEDIA LIBRARY STATISTICS
  // ==========================================

  getStats(): Observable<MediaStatsResponse> {
    return this.http.get<MediaStatsResponse>(
      `${this.baseUrl}/stats`,
      this.options()
    );
  }


  // ==========================================
  // SINGLE IMAGE DETAILS
  // ==========================================

  getMediaDetails(
    mediaId: string
  ): Observable<MediaDetails> {
    return this.http.get<MediaDetails>(
      `${this.baseUrl}/media/${encodeURIComponent(mediaId)}`,
      this.options()
    );
  }


  // ==========================================
  // UPLOAD IMAGE
  // ==========================================

  upload(image: File): Observable<UploadImageResponse> {
    const form = new FormData();

    form.append(
      'image',
      image,
      image.name
    );

    return this.http.post<UploadImageResponse>(
      `${this.baseUrl}/upload`,
      form,
      this.options()
    );
  }


  // ==========================================
  // DELETE UNUSED IMAGE PERMANENTLY
  // ==========================================

  deleteUnused(
    publicId: string
  ): Observable<{ message: string }> {

    return this.http.delete<{ message: string }>(
      `${this.baseUrl}/unused`,
      {
        ...this.options(),
        params: new HttpParams().set(
          'public_id',
          publicId
        )
      }
    );
  }


  // ==========================================
  // MAKE IMAGE PROJECT COVER
  // ==========================================

  selectCover(
    projectId: string,
    mediaId: string
  ): Observable<unknown> {

    return this.http.post(
      `${this.baseUrl}/projects/${encodeURIComponent(projectId)}/cover/select`,
      {
        media_id: mediaId
      },
      this.options()
    );
  }


  // ==========================================
  // ADD IMAGES TO PROJECT GALLERY
  // ==========================================

  selectGallery(
    projectId: string,
    mediaIds: string[]
  ): Observable<unknown> {

    return this.http.post(
      `${this.baseUrl}/projects/${encodeURIComponent(projectId)}/gallery/select`,
      {
        media_ids: mediaIds
      },
      this.options()
    );
  }


  // ==========================================
  // REMOVE IMAGE FROM PROJECT GALLERY
  // Original remains in Media Library.
  // ==========================================

  removeFromGallery(
    projectId: string,
    publicId: string
  ): Observable<{ message: string }> {

    return this.http.delete<{ message: string }>(
      `${this.baseUrl}/projects/${encodeURIComponent(projectId)}/gallery`,
      {
        ...this.options(),
        params: new HttpParams().set(
          'public_id',
          publicId
        )
      }
    );
  }


  // ==========================================
  // SAVE GALLERY IMAGE ORDER
  // ==========================================

  saveGalleryOrder(
    projectId: string,
    orderedUrls: string[]
  ): Observable<GalleryOrderResponse> {

    return this.http.put<GalleryOrderResponse>(
      `${this.baseUrl}/projects/${encodeURIComponent(projectId)}/gallery/order`,
      {
        ordered_urls: orderedUrls
      },
      this.options()
    );
  }

  removeCover(projectId: string) {
    return this.http.delete(
      `${this.baseUrl}/projects/${encodeURIComponent(projectId)}/cover`,
      this.options()
    );
  }

}

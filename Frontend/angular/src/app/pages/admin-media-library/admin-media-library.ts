
import {
  Component,
  ChangeDetectorRef,
  inject,
  OnInit,
  PLATFORM_ID
} from '@angular/core';

import { isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpClient, HttpParams } from '@angular/common/http';

import {
  EMPTY,
  expand,
  finalize,
  forkJoin,
  reduce,
  switchMap,
  throwError
} from 'rxjs';

import {
  AdminMediaService,
  MediaImage,
  MediaDetails,
  MediaStatsResponse,
  ImageUsage,
  ImageSort
} from '../../services/admin-media';

type LibraryTab = 'images' | 'galleries';

interface GalleryAsset {
  url: string;
  public_id: string;
}

interface ProjectOption {
  id: string;
  name: string;
  image?: string | null;
  gallery?: string[];
  gallery_assets?: GalleryAsset[];
}

interface ProjectListResponse {
  projects: ProjectOption[];
  current_page: number;
  total_pages: number;
}

@Component({
  selector: 'app-admin-media-library',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './admin-media-library.html',
  styleUrl: './admin-media-library.scss'
})
export class AdminMediaLibrary implements OnInit {

  private mediaService = inject(AdminMediaService);
  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);
  private platformId = inject(PLATFORM_ID);

  private readonly projectsUrl =
    'http://127.0.0.1:8000/projects/';

  activeTab: LibraryTab = 'images';
  openedGalleryId = '';

  images: MediaImage[] = [];
  stats: MediaStatsResponse | null = null;

  loading = false;
  uploading = false;
  actionLoading = false;

  error = '';
  success = '';

  search = '';
  usage: ImageUsage = 'all';
  sortBy: ImageSort = 'newest';

  page = 1;
  limit = 20;
  total = 0;
  totalPages = 0;

  selectedImage: MediaImage | null = null;
  selectedMediaIds: string[] = [];

  projects: ProjectOption[] = [];
  projectId = '';
  projectSearch = '';
  loadingProjects = false;
  projectsError = '';

  galleryPreviewUrl: string | null = null;

  // Non-destructive crop editor
  cropSourceUrl: string | null = null;
  cropPreviewUrl: string | null = null;
  cropLoading = false;
  cropSaving = false;
  cropError = '';
  cropX = 0;
  cropY = 0;
  cropWidth = 100;
  cropHeight = 100;
  cropSourceImage: HTMLImageElement | null = null;
  private cropLoadSequence = 0;
  private cropLoadTimer: ReturnType<typeof setTimeout> | null = null;
  private cropDrag: {
    pointerId: number;
    mode: 'new' | 'move' | 'nw' | 'ne' | 'sw' | 'se';
    startX: number;
    startY: number;
    x: number;
    y: number;
    width: number;
    height: number;
    rect: DOMRect;
  } | null = null;


  // ==========================================
  // GALLERY MANAGEMENT STATE
  // ==========================================

  openMenuUrl: string | null = null;
  galleryOrder: string[] = [];
  savingOrder = false;
  draggingIndex: number | null = null;

  imageDetails: MediaDetails | null = null;
  imageInfoUrl: string | null = null;
  loadingImageInfo = false;

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.loadMedia();
      this.loadProjects();
    }
  }

  // ==========================================
  // NAVIGATION
  // ==========================================

  showImages(): void {
    this.activeTab = 'images';
    this.openedGalleryId = '';
    this.galleryPreviewUrl = null;
    this.openMenuUrl = null;
    this.error = '';
  }

  showGalleries(): void {
    this.activeTab = 'galleries';
    this.openedGalleryId = '';
    this.selectedImage = null;
    this.openMenuUrl = null;
    this.error = '';
  }

  openGalleryFolder(projectId: string): void {
    const project = this.projects.find(
      item => item.id === projectId
    );

    if (!project) {
      return;
    }

    this.openedGalleryId = projectId;
    this.projectId = projectId;
    this.galleryOrder = this.getGalleryImages(project);
    this.galleryPreviewUrl = null;
    this.openMenuUrl = null;
    this.error = '';
  }

  closeGalleryFolder(): void {
    this.openedGalleryId = '';
    this.galleryPreviewUrl = null;
    this.openMenuUrl = null;
    this.galleryOrder = [];
  }

  openGalleryPreview(url: string): void {
    this.openMenuUrl = null;
    this.galleryPreviewUrl = url;
  }

  closeGalleryPreview(): void {
    this.galleryPreviewUrl = null;
  }

  // ==========================================
  // PROJECT GALLERY DATA
  // ==========================================

  get filteredProjects(): ProjectOption[] {
    const keyword = this.projectSearch.trim().toLowerCase();

    return keyword
      ? this.projects.filter(project =>
          project.name.toLowerCase().includes(keyword)
        )
      : this.projects;
  }

  get selectedProjectName(): string {
    return this.projects.find(
      project => project.id === this.projectId
    )?.name ?? '';
  }

  get openedGallery(): ProjectOption | null {
    return this.projects.find(
      project => project.id === this.openedGalleryId
    ) ?? null;
  }

  get totalProjectGalleryImages(): number {
    return this.projects.reduce(
      (total, project) =>
        total + this.getGalleryImages(project).length,
      0
    );
  }

  getGalleryImages(project: ProjectOption): string[] {
    const urls = [
      ...(project.gallery ?? []),
      ...(project.gallery_assets ?? []).map(
        asset => asset.url
      )
    ];

    return [...new Set(
      urls.filter(
        (url): url is string =>
          typeof url === 'string' && url.length > 0
      )
    )];
  }

  
  getGalleryThumbnail(project: ProjectOption): string | null {
    return project.image ||
      this.getGalleryImages(project)[0] ||
      null;
  }

  getGalleryPublicId(url: string): string | null {
    const project = this.openedGallery;

    if (!project) {
      return null;
    }

    return project.gallery_assets?.find(
      asset => asset.url === url
    )?.public_id ?? null;
  }

  // ==========================================
  // LOAD PROJECTS
  // ==========================================

  loadProjects(): void {
    this.loadingProjects = true;
    this.projectsError = '';

    const fetchPage = (page: number) =>
      this.http.get<ProjectListResponse>(
        this.projectsUrl,
        {
          params: new HttpParams()
            .set('page', page)
            .set('limit', 100)
            .set('sort_by', 'name_asc')
        }
      );

    fetchPage(1)
      .pipe(
        expand(response =>
          response.current_page < response.total_pages
            ? fetchPage(response.current_page + 1)
            : EMPTY
        ),
        reduce(
          (all, response) => [
            ...all,
            ...response.projects
          ],
          [] as ProjectOption[]
        ),
        finalize(() => {
          this.loadingProjects = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: projects => {
          this.projects = projects;

          if (this.openedGalleryId) {
            const current = this.openedGallery;

            if (current) {
              this.galleryOrder =
                this.getGalleryImages(current);
            } else {
              this.closeGalleryFolder();
            }
          }

          this.cdr.detectChanges();
        },
        error: () => {
          this.projectsError =
            'Unable to load project galleries.';
        }
      });
  }

  // ==========================================
  // LOAD INDIVIDUAL IMAGES
  // ==========================================

  loadMedia(): void {
    this.loading = true;
    this.error = '';

    forkJoin({
      library: this.mediaService.getImages({
        page: this.page,
        limit: this.limit,
        search: this.search,
        usage: this.usage,
        sort_by: this.sortBy
      }),
      stats: this.mediaService.getStats()
    })
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: ({ library, stats }) => {
          this.images = library.images;
          this.total = library.total;
          this.totalPages = library.total_pages;
          this.stats = stats;
          this.cdr.detectChanges();
        },
        error: () => {
          this.error = 'Unable to load Media Library.';
        }
      });
  }

  applyFilters(): void {
    this.page = 1;
    this.loadMedia();
  }

  nextPage(): void {
    if (this.page < this.totalPages) {
      this.page++;
      this.loadMedia();
    }
  }

  previousPage(): void {
    if (this.page > 1) {
      this.page--;
      this.loadMedia();
    }
  }

  // ==========================================
  // UPLOAD
  // ==========================================

  uploadFiles(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
      return;
    }

    this.error = '';
    this.success = '';

    if (![
      'image/jpeg',
      'image/png',
      'image/webp'
    ].includes(file.type)) {
      this.error = 'Only JPG, PNG and WebP are allowed.';
      input.value = '';
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.error = 'Maximum file size is 10 MB.';
      input.value = '';
      return;
    }

    this.uploading = true;

    this.mediaService.upload(file)
      .pipe(
        finalize(() => {
          this.uploading = false;
          input.value = '';
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.success = 'Image uploaded successfully.';
          this.page = 1;
          this.loadMedia();
        },
        error: () => {
          this.error = 'Image upload failed.';
        }
      });
  }

  // ==========================================
  // IMAGE PREVIEW
  // ==========================================

  openPreview(image: MediaImage): void {
    this.selectedImage = image;
  }

  closePreview(): void {
    this.selectedImage = null;
  }

  // ==========================================
  // NON-DESTRUCTIVE IMAGE CROPPING
  // ==========================================

  openCropEditor(url: string): void {
    if (!isPlatformBrowser(this.platformId)) return;

    this.closePreview();
    this.closeGalleryPreview();
    this.closeImageMenu();
    this.coverMenuOpen = false;
    this.cropSourceUrl = url;
    this.cropPreviewUrl = null;
    this.cropSourceImage = null;
    this.cropError = '';
    this.cropDrag = null;
    this.cropX = 0;
    this.cropY = 0;
    this.cropWidth = 100;
    this.cropHeight = 100;
    this.cropLoading = true;
    this.loadCropSource(url);
  }

  private loadCropSource(url: string): void {
    const sequence = ++this.cropLoadSequence;
    if (this.cropLoadTimer !== null) {
      clearTimeout(this.cropLoadTimer);
      this.cropLoadTimer = null;
    }

    const finishWithError = (message: string): void => {
      if (sequence !== this.cropLoadSequence) return;
      if (this.cropLoadTimer !== null) {
        clearTimeout(this.cropLoadTimer);
        this.cropLoadTimer = null;
      }
      this.cropLoading = false;
      this.cropError = message;
      this.cdr.detectChanges();
    };

    const source = new Image();
    // Cross-origin pixels can only be exported when the image server allows CORS.
    source.crossOrigin = 'anonymous';
    source.onload = () => {
      if (sequence !== this.cropLoadSequence) return;
      if (this.cropLoadTimer !== null) {
        clearTimeout(this.cropLoadTimer);
        this.cropLoadTimer = null;
      }
      if (!source.naturalWidth || !source.naturalHeight) {
        finishWithError('The image has no valid dimensions.');
        return;
      }
      this.cropSourceImage = source;
      this.cropLoading = false;
      this.resetCrop();
      this.cdr.detectChanges();
    };
    source.onerror = () => finishWithError(
      'Image loading failed. The image host may be blocking cross-origin access. Check the Network tab for the image request.'
    );

    this.cropLoadTimer = setTimeout(() => {
      finishWithError(
        'Image request timed out. Please check Cloudinary connectivity and CORS in DevTools → Network.'
      );
    }, 12000);

    // Avoid reusing a browser-cached response that was fetched without CORS headers.
    // This is safe for the public Cloudinary image URLs used in the Media Library.
    const separator = url.includes('?') ? '&' : '?';
    source.src = `${url}${separator}crop_cache=${Date.now()}`;
  }

  retryCropImage(): void {
    if (!this.cropSourceUrl || this.cropLoading || this.cropSaving) return;
    this.cropError = '';
    this.cropLoading = true;
    this.loadCropSource(this.cropSourceUrl);
  }

  closeCropEditor(): void {
    ++this.cropLoadSequence;
    if (this.cropLoadTimer !== null) {
      clearTimeout(this.cropLoadTimer);
      this.cropLoadTimer = null;
    }
    this.cropSourceUrl = null;
    this.cropPreviewUrl = null;
    this.cropSourceImage = null;
    this.cropError = '';
    this.cropLoading = false;
    this.cropDrag = null;
  }

  resetCrop(): void {
    const source = this.cropSourceImage;
    if (!source) return;
    // Start with a centered, visually square crop box.
    const side = 0.7 * Math.min(source.naturalWidth, source.naturalHeight);
    this.cropWidth = 100 * side / source.naturalWidth;
    this.cropHeight = 100 * side / source.naturalHeight;
    this.cropX = (100 - this.cropWidth) / 2;
    this.cropY = (100 - this.cropHeight) / 2;
    this.refreshCropPreview();
  }

  startCropPointer(
    event: PointerEvent,
    mode: 'new' | 'move' | 'nw' | 'ne' | 'sw' | 'se'
  ): void {
    if (this.cropSaving || !this.cropSourceImage || !event.isPrimary) return;
    const stage = (event.currentTarget as HTMLElement).closest('.crop-stage') as HTMLElement | null;
    if (!stage) return;
    const rect = stage.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    event.preventDefault();
    event.stopPropagation();
    this.cropDrag = {
      pointerId: event.pointerId, mode,
      startX: this.clamp((event.clientX - rect.left) / rect.width * 100, 0, 100),
      startY: this.clamp((event.clientY - rect.top) / rect.height * 100, 0, 100),
      x: this.cropX, y: this.cropY,
      width: this.cropWidth, height: this.cropHeight, rect
    };
    stage.setPointerCapture(event.pointerId);
    if (mode === 'new') {
      this.cropX = this.cropDrag.startX;
      this.cropY = this.cropDrag.startY;
      this.cropWidth = Math.min(5, 100 - this.cropX);
      this.cropHeight = Math.min(5, 100 - this.cropY);
    }
  }

  updateCropPointer(event: PointerEvent): void {
    const drag = this.cropDrag;
    if (!drag || event.pointerId !== drag.pointerId) return;
    event.preventDefault();
    const px = this.clamp((event.clientX - drag.rect.left) / drag.rect.width * 100, 0, 100);
    const py = this.clamp((event.clientY - drag.rect.top) / drag.rect.height * 100, 0, 100);
    const dx = px - drag.startX;
    const dy = py - drag.startY;
    const min = 2;
    if (drag.mode === 'move') {
      this.cropX = this.clamp(drag.x + dx, 0, 100 - drag.width);
      this.cropY = this.clamp(drag.y + dy, 0, 100 - drag.height);
      return;
    }
    if (drag.mode === 'new') {
      this.cropX = Math.min(px, drag.startX);
      this.cropY = Math.min(py, drag.startY);
      this.cropWidth = Math.max(min, Math.abs(px - drag.startX));
      this.cropHeight = Math.max(min, Math.abs(py - drag.startY));
      this.cropWidth = Math.min(this.cropWidth, 100 - this.cropX);
      this.cropHeight = Math.min(this.cropHeight, 100 - this.cropY);
      return;
    }
    let left = drag.x, right = drag.x + drag.width;
    let top = drag.y, bottom = drag.y + drag.height;
    if (drag.mode.includes('w')) left = this.clamp(px, 0, right - min);
    if (drag.mode.includes('e')) right = this.clamp(px, left + min, 100);
    if (drag.mode.includes('n')) top = this.clamp(py, 0, bottom - min);
    if (drag.mode.includes('s')) bottom = this.clamp(py, top + min, 100);
    this.cropX = left;
    this.cropY = top;
    this.cropWidth = right - left;
    this.cropHeight = bottom - top;
  }

  finishCropPointer(event: PointerEvent): void {
    if (!this.cropDrag || this.cropDrag.pointerId !== event.pointerId) return;
    this.cropDrag = null;
    this.refreshCropPreview();
  }

  private clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value));
  }

  refreshCropPreview(): void {
    const source = this.cropSourceImage;
    if (!source) return;
    this.cropError = '';

    // Always keep the crop rectangle inside the original picture.
    this.cropWidth = Math.min(100, Math.max(5, Number(this.cropWidth)));
    this.cropHeight = Math.min(100, Math.max(5, Number(this.cropHeight)));
    this.cropX = Math.min(100 - this.cropWidth, Math.max(0, Number(this.cropX)));
    this.cropY = Math.min(100 - this.cropHeight, Math.max(0, Number(this.cropY)));

    try {
      const canvas = this.drawCroppedImage(1000);
      this.cropPreviewUrl = canvas.toDataURL('image/jpeg', 0.88);
    } catch {
      this.cropPreviewUrl = null;
      this.cropError = 'Crop preview is blocked by image security settings (CORS).';
    }
  }

  private drawCroppedImage(maxEdge?: number): HTMLCanvasElement {
    const source = this.cropSourceImage;
    if (!source) throw new Error('Image not loaded');

    const sx = Math.round(source.naturalWidth * this.cropX / 100);
    const sy = Math.round(source.naturalHeight * this.cropY / 100);
    const sw = Math.max(1, Math.min(source.naturalWidth - sx,
      Math.round(source.naturalWidth * this.cropWidth / 100)));
    const sh = Math.max(1, Math.min(source.naturalHeight - sy,
      Math.round(source.naturalHeight * this.cropHeight / 100)));

    const scale = maxEdge ? Math.min(1, maxEdge / Math.max(sw, sh)) : 1;
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(sw * scale));
    canvas.height = Math.max(1, Math.round(sh * scale));

    const context = canvas.getContext('2d');
    if (!context) throw new Error('Canvas is unavailable');
    context.drawImage(source, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    return canvas;
  }

  saveCroppedImage(): void {
    if (!this.cropSourceImage || this.cropSaving || this.cropError) return;
    this.cropSaving = true;
    this.error = '';
    this.success = '';

    try {
      const canvas = this.drawCroppedImage();
      canvas.toBlob(blob => {
        if (!blob) {
          this.cropSaving = false;
          this.cropError = 'Unable to create the cropped image.';
          this.cdr.detectChanges();
          return;
        }

        const file = new File([blob], `cropped-${Date.now()}.jpg`, {
          type: 'image/jpeg'
        });
        if (file.size > 10 * 1024 * 1024) {
          this.cropSaving = false;
          this.cropError = 'Cropped image exceeds the 10 MB upload limit.';
          this.cdr.detectChanges();
          return;
        }

        this.mediaService.upload(file).pipe(finalize(() => {
          this.cropSaving = false;
          this.cdr.detectChanges();
        })).subscribe({
          next: () => {
            this.closeCropEditor();
            this.success = 'Cropped image saved as a new Media Library image. Original preserved.';
            this.page = 1;
            this.loadMedia();
          },
          error: () => {
            this.cropError = 'Could not upload the cropped image.';
          }
        });
      }, 'image/jpeg', 0.92);
    } catch {
      this.cropSaving = false;
      this.cropError = 'Unable to export this image. The image host may block canvas access.';
    }
  }

  // ==========================================
  // DELETE UNUSED IMAGE
  // ==========================================

  deleteImage(image: MediaImage): void {
    if (image.in_use) {
      this.error =
        'This image is being used by a project.';
      return;
    }

    if (!confirm(
      'Permanently delete this unused image?'
    )) {
      return;
    }

    this.actionLoading = true;
    this.error = '';
    this.success = '';

    this.mediaService.deleteUnused(image.public_id)
      .pipe(
        finalize(() => {
          this.actionLoading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.success = 'Image permanently deleted.';
          this.selectedImage = null;

          this.selectedMediaIds =
            this.selectedMediaIds.filter(
              id => id !== image.id
            );

          this.loadMedia();
        },
        error: () => {
          this.error = 'Unable to delete image.';
        }
      });
  }

  // ==========================================
  // IMAGE SELECTION
  // ==========================================

  toggleSelection(mediaId: string): void {
    if (this.selectedMediaIds.includes(mediaId)) {
      this.selectedMediaIds =
        this.selectedMediaIds.filter(
          id => id !== mediaId
        );
      return;
    }

    if (this.selectedMediaIds.length >= 20) {
      this.error = 'Maximum 20 images can be selected.';
      return;
    }

    this.selectedMediaIds.push(mediaId);
  }

  isSelected(mediaId: string): boolean {
    return this.selectedMediaIds.includes(mediaId);
  }

  assignCover(image: MediaImage): void {
    if (!this.projectId) {
      this.error = 'Select a project first.';
      return;
    }

    this.actionLoading = true;
    this.error = '';
    this.success = '';

    this.mediaService.selectCover(
      this.projectId,
      image.id
    )
      .pipe(
        finalize(() => {
          this.actionLoading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.success =
            `Cover updated for ${this.selectedProjectName}.`;
          this.loadMedia();
          this.loadProjects();
        },
        error: () => {
          this.error = 'Unable to assign project cover.';
        }
      });
  }

  assignGallery(): void {
    if (!this.projectId) {
      this.error = 'Select a project first.';
      return;
    }

    if (!this.selectedMediaIds.length) {
      this.error = 'Select at least one image.';
      return;
    }

    this.actionLoading = true;
    this.error = '';
    this.success = '';

    this.mediaService.selectGallery(
      this.projectId,
      this.selectedMediaIds
    )
      .pipe(
        finalize(() => {
          this.actionLoading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.success =
            `Gallery updated for ${this.selectedProjectName}.`;

          this.selectedMediaIds = [];
          this.loadMedia();
          this.loadProjects();
        },
        error: () => {
          this.error = 'Unable to assign gallery images.';
        }
      });
  }

  // ==========================================
  // THREE-DOT MENU
  // ==========================================

  toggleImageMenu(url: string): void {
    this.openMenuUrl =
      this.openMenuUrl === url ? null : url;
  }

  closeImageMenu(): void {
    this.openMenuUrl = null;
  }

  // ==========================================
  // REORDER GALLERY
  // ==========================================

  get hasUnsavedOrder(): boolean {
    const project = this.openedGallery;

    if (!project) {
      return false;
    }

    const original = this.getGalleryImages(project);

    return JSON.stringify(original) !==
      JSON.stringify(this.galleryOrder);
  }

  moveGalleryImage(
    index: number,
    direction: -1 | 1
  ): void {
    const destination = index + direction;

    if (
      destination < 0 ||
      destination >= this.galleryOrder.length
    ) {
      return;
    }

    const updated = [...this.galleryOrder];

    [
      updated[index],
      updated[destination]
    ] = [
      updated[destination],
      updated[index]
    ];

    this.galleryOrder = updated;
    this.closeImageMenu();
  }

  moveToFirst(url: string): void {
    const index = this.galleryOrder.indexOf(url);

    if (index <= 0) {
      return;
    }

    this.galleryOrder = [
      url,
      ...this.galleryOrder.filter(item => item !== url)
    ];

    this.closeImageMenu();
  }

  onGalleryDragStart(index: number): void {
    if (this.savingOrder || this.actionLoading) {
      return;
    }

    this.draggingIndex = index;
  }

  onGalleryDragOver(event: DragEvent): void {
    if (this.draggingIndex !== null) {
      event.preventDefault();
    }
  }

  onGalleryDrop(event: DragEvent, target: number): void {
    event.preventDefault();

    const source = this.draggingIndex;
    this.draggingIndex = null;

    if (
      source === null ||
      source === target ||
      source < 0 ||
      target < 0 ||
      source >= this.galleryOrder.length ||
      target >= this.galleryOrder.length
    ) {
      return;
    }

    const updated = [...this.galleryOrder];
    const [moved] = updated.splice(source, 1);

    updated.splice(target, 0, moved);
    this.galleryOrder = updated;
  }

  onGalleryDragEnd(): void {
    this.draggingIndex = null;
  }

  discardGalleryOrder(): void {
    const project = this.openedGallery;

    if (project) {
      this.galleryOrder = this.getGalleryImages(project);
    }
  }

  saveGalleryOrder(): void {
    if (
      !this.openedGalleryId ||
      !this.hasUnsavedOrder ||
      this.savingOrder
    ) {
      return;
    }

    this.savingOrder = true;
    this.error = '';
    this.success = '';

    this.mediaService.saveGalleryOrder(
      this.openedGalleryId,
      [...this.galleryOrder]
    )
      .pipe(
        finalize(() => {
          this.savingOrder = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.success = 'Gallery order saved successfully.';
          this.loadProjects();
        },
        error: () => {
          this.error =
            'Unable to save order. Refresh the gallery and retry.';
        }
      });
  }

  // ==========================================
  // MAKE GALLERY IMAGE THE PROJECT COVER
  // ==========================================

  makeGalleryCover(url: string): void {
    const project = this.openedGallery;
    const publicId = this.getGalleryPublicId(url);

    if (!project || !publicId) {
      this.error =
        'This image has no Media Library reference.';
      return;
    }

    this.actionLoading = true;
    this.error = '';
    this.success = '';
    this.closeImageMenu();

    // Resolve the gallery image's Media Library ID.
    this.mediaService.getImages({
      page: 1,
      limit: 100,
      search: publicId,
      usage: 'all',
      sort_by: 'newest'
    })
      .pipe(
        switchMap(response => {
          const media = response.images.find(
            item => item.public_id === publicId
          );

          if (!media) {
            return throwError(() =>
              new Error('Media Library image not found')
            );
          }

          return this.mediaService.selectCover(
            project.id,
            media.id
          );
        }),
        finalize(() => {
          this.actionLoading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.success =
            'Project cover changed successfully.';
          this.loadProjects();
          this.loadMedia();
        },
        error: () => {
          this.error =
            'Unable to set this image as the cover.';
        }
      });
  }

  // ==========================================
  // REMOVE IMAGE FROM THE GALLERY
  // ==========================================

  removeGalleryImage(url: string): void {
    const project = this.openedGallery;
    const publicId = this.getGalleryPublicId(url);

    if (!project || !publicId) {
      this.error =
        'This image cannot be removed automatically because its metadata is missing.';
      return;
    }

    if (this.hasUnsavedOrder) {
      this.error =
        'Save or discard your gallery order before removing images.';
      return;
    }

    if (!confirm(
      'Remove this image from the project gallery? The original will remain in Media Library.'
    )) {
      return;
    }

    this.actionLoading = true;
    this.error = '';
    this.success = '';
    this.closeImageMenu();

    this.mediaService.removeFromGallery(
      project.id,
      publicId
    )
      .pipe(
        finalize(() => {
          this.actionLoading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: () => {
          this.success =
            'Image removed from the gallery.';

          this.loadProjects();
          this.loadMedia();
        },
        error: () => {
          this.error =
            'Unable to remove this gallery image.';
        }
      });
  }

  // ==========================================
  // ABOUT IMAGE
  // ==========================================

  showGalleryImageInfo(url: string): void {
    const publicId = this.getGalleryPublicId(url);

    this.closeImageMenu();
    this.imageInfoUrl = url;
    this.imageDetails = null;

    if (!publicId) {
      return;
    }

    this.loadingImageInfo = true;

    this.mediaService.getImages({
      page: 1,
      limit: 100,
      search: publicId,
      usage: 'all',
      sort_by: 'newest'
    })
      .pipe(
        switchMap(response => {
          const media = response.images.find(
            item => item.public_id === publicId
          );

          if (!media) {
            return throwError(() =>
              new Error('Image not found')
            );
          }

          return this.mediaService.getMediaDetails(
            media.id
          );
        }),
        finalize(() => {
          this.loadingImageInfo = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: details => {
          this.imageDetails = details;
        },
        error: () => {
          this.imageDetails = null;
        }
      });
  }

  closeImageInfo(): void {
    this.imageInfoUrl = null;
    this.imageDetails = null;
  }

coverMenuOpen = false;

changeCover(): void {
  const project = this.openedGallery;
  if (!project) return;

  this.projectId = project.id;
  this.coverMenuOpen = false;
  this.showImages();
}

removeCover(): void {
  const project = this.openedGallery;
  if (!project || this.actionLoading) return;

  if (!confirm('Remove this project cover? The original image will be kept.')) {
    return;
  }

  this.actionLoading = true;
  this.coverMenuOpen = false;

  this.mediaService.removeCover(project.id)
    .pipe(finalize(() => {
      this.actionLoading = false;
      this.cdr.detectChanges();
    }))
    .subscribe({
      next: () => {
        this.success = 'Cover removed successfully.';
        this.loadProjects();
        this.loadMedia();
      },
      error: () => {
        this.error = 'Unable to remove project cover.';
      }
    });
}

  
}

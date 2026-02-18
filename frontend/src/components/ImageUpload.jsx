import { useState, useRef } from 'react'
import ReactCrop, { centerCrop, makeAspectCrop, convertToPixelCrop } from 'react-image-crop'
import 'react-image-crop/dist/ReactCrop.css'
import './ImageUpload.css'

function centerAspectCrop(mediaWidth, mediaHeight, aspect) {
  return centerCrop(
    makeAspectCrop(
      {
        unit: '%',
        width: 90,
      },
      aspect,
      mediaWidth,
      mediaHeight,
    ),
    mediaWidth,
    mediaHeight,
  )
}

function ImageUpload({ onUpload }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isUploading, setIsUploading] = useState(false)

  // Crop state
  const [crop, setCrop] = useState()
  const [completedCrop, setCompletedCrop] = useState()
  const imgRef = useRef(null)

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setCrop(undefined) // Reset crop
      const file = e.target.files[0]
      setSelectedFile(file)

      // Create preview URL
      const reader = new FileReader()
      reader.addEventListener('load', () => setPreviewUrl(reader.result))
      reader.readAsDataURL(file)
    }
  }

  const onImageLoad = (e) => {
    const { width, height } = e.currentTarget
    setCrop(centerAspectCrop(width, height, 16 / 9))
  }

  const getCroppedImg = (image, crop) => {
    const canvas = document.createElement('canvas')
    const scaleX = image.naturalWidth / image.width
    const scaleY = image.naturalHeight / image.height
    canvas.width = crop.width
    canvas.height = crop.height
    const ctx = canvas.getContext('2d')

    ctx.drawImage(
      image,
      crop.x * scaleX,
      crop.y * scaleY,
      crop.width * scaleX,
      crop.height * scaleY,
      0,
      0,
      crop.width,
      crop.height,
    )

    return new Promise((resolve, reject) => {
      canvas.toBlob(blob => {
        if (!blob) {
          reject(new Error('Canvas is empty'))
          return
        }
        blob.name = 'cropped.jpg'
        resolve(blob)
      }, 'image/jpeg')
    })
  }

  const handleUpload = async () => {
    if (!selectedFile && !previewUrl) return

    setIsUploading(true)
    try {
      let fileToUpload = selectedFile

      // If we have a completed crop, use that instead of the original file
      if (completedCrop && imgRef.current) {
        // Convert to pixel crop if it is percentage
        const pixelCrop = completedCrop.unit === '%'
          ? convertToPixelCrop(completedCrop, imgRef.current.width, imgRef.current.height)
          : completedCrop

        if (pixelCrop.width && pixelCrop.height) {
          const blob = await getCroppedImg(imgRef.current, pixelCrop)
          fileToUpload = new File([blob], selectedFile?.name || 'image.jpg', { type: blob.type })
        }
      }

      await onUpload(fileToUpload)

      // Clear after successful upload
      handleClear()
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
    setCompletedCrop(null)
    setCrop(undefined)
  }

  return (
    <div className="image-upload-container">
      <h3>Upload Image</h3>

      {!previewUrl ? (
        <div className="upload-input-area">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            id="file-upload"
            className="file-input"
          />
          <label htmlFor="file-upload" className="file-label">
            Choose an image
          </label>
        </div>
      ) : (
        <div className="preview-area">
          <div className="image-preview">
            <ReactCrop
              crop={crop}
              onChange={(_, percentCrop) => setCrop(percentCrop)}
              onComplete={(c) => setCompletedCrop(c)}
              aspect={undefined} // Allow free cropping, or set to 16/9 etc.
            >
              <img
                ref={imgRef}
                src={previewUrl}
                alt="Preview"
                onLoad={onImageLoad}
                style={{ maxWidth: '100%', maxHeight: '400px' }}
              />
            </ReactCrop>
          </div>

          <div className="actions">
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="upload-btn"
            >
              {isUploading ? 'Uploading...' : 'Upload'}
            </button>
            <button
              onClick={handleClear}
              disabled={isUploading}
              className="clear-btn"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ImageUpload
